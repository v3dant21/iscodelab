"""Short-lived recovery links; no tokens or passwords in API responses."""
import logging
import hashlib
import secrets
import time
from sqlalchemy import select,delete,update
from fastapi import Request,Depends
from pydantic import BaseModel,ConfigDict,Field
from models import User,Session,PasswordReset
from personal_data import lookup
import email_delivery

class RecoveryEmail(BaseModel):
    model_config=ConfigDict(extra='forbid')
    email:str=Field(min_length=5,max_length=254,pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

class NewPassword(BaseModel):
    model_config=ConfigDict(extra='forbid')
    token:str=Field(min_length=32,max_length=128)
    password:str=Field(min_length=12,max_length=128)

def replace_password(db,user,password,hasher):
    user.password=hasher.hash(password)
    db.execute(delete(Session).where(Session.user_id==user.id))
    db.execute(update(PasswordReset).where(PasswordReset.user_id==user.id).values(used=True))

def register(app,database,fail,origin,hasher):
    def check_origin(request):
        if request.headers.get('origin') not in (None,origin):fail('Origin not allowed.',403)

    @app.post('/auth/password/forgot')
    def forgot(body:RecoveryEmail,request:Request,db=Depends(database)):
        check_origin(request)
        if not email_delivery.configured():
            fail('Password recovery email is not connected yet. Contact the restaurant administrator for an account reset.',503)
        message={'message':'If an account matches this email, a reset link will arrive shortly. Check your spam folder.'}
        user=db.scalar(select(User).where(User.email_hash==lookup(body.email)).with_for_update())
        if not user:return message
        now=time.time()
        latest=db.scalar(select(PasswordReset).where(PasswordReset.user_id==user.id).order_by(PasswordReset.created.desc()).limit(1))
        if latest and latest.created>now-300:return message
        token=secrets.token_urlsafe(32);hashed=hashlib.sha256(token.encode()).hexdigest()
        db.execute(update(PasswordReset).where(PasswordReset.user_id==user.id).values(used=True))
        db.add(PasswordReset(token_hash=hashed,user_id=user.id,created=now,expires=now+1800,used=False))
        db.commit()
        try:
            email_delivery.send({'from':__import__('os').environ['EMAIL_FROM'],'to':[user.email],
                'subject':'Reset your Dum & Dastaan password',
                'text':'Choose a new password using this single-use link. It expires in 30 minutes. If you did not request this, ignore this email.\n\n'+email_delivery.website()+'/reset-password#token='+token},'reset:'+hashed)
        except Exception:
            # Same response for all recipients; do not expose provider or account details.
            logging.warning("Password recovery email submission failed")
        return message

    @app.post('/auth/password/reset')
    def reset(body:NewPassword,request:Request,db=Depends(database)):
        check_origin(request)
        hashed=hashlib.sha256(body.token.encode()).hexdigest()
        record=db.get(PasswordReset,hashed)
        if not record:fail('Reset link is invalid or expired. Request a new one.',400)
        user=db.scalar(select(User).where(User.id==record.user_id).with_for_update())
        # Atomic consumption also protects against duplicate submissions.
        consumed=db.execute(update(PasswordReset).where(PasswordReset.token_hash==hashed,
            PasswordReset.used.is_(False),PasswordReset.expires>time.time()).values(used=True))
        if consumed.rowcount!=1:fail('Reset link is invalid or expired. Request a new one.',400)
        replace_password(db,user,body.password,hasher)
        db.commit()
        return {'message':'Password updated. Sign in with your new password.'}
