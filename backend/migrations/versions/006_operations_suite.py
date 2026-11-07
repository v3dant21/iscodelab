"""Central catalogue controls, kitchen timestamps, loyalty ledger and catering."""
from alembic import op
import sqlalchemy as sa
from models import LoyaltyEntry, PartyRequest
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    def add(table, column):
        if column.name not in {c['name'] for c in sa.inspect(op.get_bind()).get_columns(table)}:
            op.add_column(table,column)
    add('outlets', sa.Column('city', sa.String(80), nullable=False, server_default='Hyderabad'))
    for name, kind, default in [('city_prices',sa.JSON(),'{}'),('schedule',sa.JSON(),'[]'),('photo_url',sa.String(1000),''),('photo_credit',sa.String(200),''),('spice_level',sa.String(20),'not_set')]:
        add('dishes',sa.Column(name,kind,nullable=False,server_default=default))
    for name in ['preparing_at','ready_at','handed_off_at','cancelled_at']:
        add('orders',sa.Column(name,sa.Float()))
    add('orders',sa.Column('cancellation_reason',sa.Text()))
    add('orders',sa.Column('handoff',sa.JSON()))
    for name in ['redeemed_points','earned_points']:
        add('orders',sa.Column(name,sa.Integer(),nullable=False,server_default='0'))
    LoyaltyEntry.__table__.create(op.get_bind(),checkfirst=True)
    PartyRequest.__table__.create(op.get_bind(),checkfirst=True)
    if 'ix_orders_outlet_created' not in {i['name'] for i in sa.inspect(op.get_bind()).get_indexes('orders')}:
        op.create_index('ix_orders_outlet_created','orders',['outlet_id','created'])


def downgrade():
    raise RuntimeError('Reward and catering records require an explicit retention plan before downgrade.')
