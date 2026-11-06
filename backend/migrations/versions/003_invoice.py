from alembic import op
from models import Invoice

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    Invoice.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    op.drop_table('invoices')
