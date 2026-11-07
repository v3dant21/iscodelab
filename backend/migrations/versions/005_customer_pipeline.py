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
    with op.batch_alter_table('users') as batch:
        batch.alter_column('email', existing_type=sa.String(254), type_=sa.Text())
        batch.add_column(sa.Column('email_hash', sa.String(64)))
        batch.add_column(sa.Column('name', sa.Text()))
        batch.add_column(sa.Column('phone', sa.Text()))
        batch.add_column(sa.Column('phone_hash', sa.String(64)))
        batch.add_column(sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.create_unique_constraint('uq_users_email_hash', ['email_hash'])
        batch.create_index('ix_users_phone_hash', ['phone_hash'])
    op.add_column('orders', sa.Column('contact', sa.JSON()))
    connection = op.get_bind()
    for row in connection.execute(sa.text('SELECT id, email FROM users')).mappings():
        connection.execute(sa.text('UPDATE users SET email_hash=:value WHERE id=:id'), {'value':lookup(decrypt(row['email'])), 'id':row['id']})
    connection.execute(sa.text('UPDATE users SET email_verified=true WHERE id IN (SELECT user_id FROM google_identities)'))
    EmailVerification.__table__.create(connection)
    EmailDelivery.__table__.create(connection)

def downgrade():
    raise RuntimeError('Encrypted customer data cannot be safely downgraded automatically.')
