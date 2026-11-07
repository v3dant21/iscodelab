"""Single-use password recovery tokens."""
from alembic import op
from models import PasswordReset
revision='007'
down_revision='006'
branch_labels=None
depends_on=None

def upgrade():
    PasswordReset.__table__.create(op.get_bind(),checkfirst=True)

def downgrade():
    PasswordReset.__table__.drop(op.get_bind(),checkfirst=True)
