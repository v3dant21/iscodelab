from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Revision 001 uses live Base metadata; checkfirst also supports fresh installs.
    sa.Table('google_identities', sa.MetaData(),
             sa.Column('subject', sa.String(255), primary_key=True),
             sa.Column('user_id', sa.Integer, nullable=False, unique=True),
             ).create(op.get_bind(), checkfirst=True)
    # Add the FK only when not already created by revision 001.
    if not sa.inspect(op.get_bind()).get_foreign_keys('google_identities'):
        op.create_foreign_key('fk_google_identity_user', 'google_identities', 'users', ['user_id'], ['id'])


def downgrade():
    op.drop_table('google_identities')
