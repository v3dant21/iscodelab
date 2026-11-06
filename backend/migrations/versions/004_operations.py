from alembic import op
import sqlalchemy as sa
from models import Notification, EstimateChange, ConsentRecord
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade():
    columns = {c['name'] for c in sa.inspect(op.get_bind()).get_columns('orders')}
    for name, kind in [('ai_minutes',sa.Integer),('original_promise',sa.Float),('late_alerted',sa.Float),('estimate_reason',sa.String)]:
        if name not in columns: op.add_column('orders',sa.Column(name,kind(),nullable=True))
    op.execute('UPDATE orders SET ai_minutes = minutes, original_promise = accepted + minutes * 60 WHERE accepted IS NOT NULL AND original_promise IS NULL')
    for table, name, kind, default in [('users','marketing_opt_in',sa.Boolean(),sa.false()),('users','marketing_updated',sa.Float(),None),('outlets','fssai',sa.String(14),None)]:
        if name not in {c['name'] for c in sa.inspect(op.get_bind()).get_columns(table)}:
            op.add_column(table,sa.Column(name,kind,nullable=default is None,server_default=default))
    ConsentRecord.__table__.create(op.get_bind(),checkfirst=True)
    Notification.__table__.create(op.get_bind(),checkfirst=True)
    EstimateChange.__table__.create(op.get_bind(),checkfirst=True)
    op.execute('CREATE INDEX IF NOT EXISTS ix_notification_dispatch ON notifications (state, next_attempt)')
    op.execute('CREATE INDEX IF NOT EXISTS ix_orders_outlet_queue ON orders (outlet_id, status, created)')

def downgrade():
    op.drop_table('consent_records')
    op.drop_column('users','marketing_opt_in'); op.drop_column('users','marketing_updated'); op.drop_column('outlets','fssai')
    op.drop_table('estimate_changes'); op.drop_table('notifications')
    for name in ('ai_minutes','original_promise','late_alerted','estimate_reason'):op.drop_column('orders',name)
