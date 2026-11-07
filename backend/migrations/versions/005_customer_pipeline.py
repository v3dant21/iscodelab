"""Add profile/index/outbox fields. Encrypt existing payloads after app rollout."""
from alembic import op
import sqlalchemy as sa
from personal_data import lookup, decrypt
from models import EmailVerification, EmailDelivery
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    connection=op.get_bind()
    columns={c['name'] for c in sa.inspect(connection).get_columns('users')}
    with op.batch_alter_table('users') as batch:
        batch.alter_column('email',existing_type=sa.String(254),type_=sa.Text())
        for name,kind,default in [('email_hash',sa.String(64),None),('name',sa.Text(),None),('phone',sa.Text(),None),('phone_hash',sa.String(64),None),('email_verified',sa.Boolean(),sa.false())]:
            if name not in columns: batch.add_column(sa.Column(name,kind,nullable=default is None,server_default=default))
        if 'email_hash' not in columns: batch.create_unique_constraint('uq_users_email_hash',['email_hash'])
        if 'phone_hash' not in columns: batch.create_index('ix_users_phone_hash',['phone_hash'])
    if 'contact' not in {c['name'] for c in sa.inspect(connection).get_columns('orders')}:
        op.add_column('orders',sa.Column('contact',sa.JSON()))
    for row in connection.execute(sa.text('SELECT id,email FROM users')).mappings():
        connection.execute(sa.text('UPDATE users SET email_hash=:value WHERE id=:id'),{'value':lookup(decrypt(row['email'])),'id':row['id']})
    connection.execute(sa.text('UPDATE users SET email_verified=true WHERE id IN (SELECT user_id FROM google_identities)'))
    EmailVerification.__table__.create(connection,checkfirst=True)
    EmailDelivery.__table__.create(connection,checkfirst=True)


def downgrade():
    raise RuntimeError('Encrypted customer data cannot be safely downgraded automatically.')
