import os
from argon2 import PasswordHasher
from sqlalchemy import text
from models import Assignment, Dish, Outlet, SessionLocal, User


def seed():
    with SessionLocal.begin() as database:
        if database.query(Outlet).first():
            sync_sequences(database)
            return
        database.add_all([Outlet(id=1, name='Kondapur', lat=17.462, lng=78.357, radius=8, minimum=20), Outlet(id=2, name='Gachibowli', lat=17.441, lng=78.349, radius=8, minimum=25), Outlet(id=3, name='Madhapur', lat=17.448, lng=78.391, radius=7, minimum=20)])
        dishes = [
            ('Dum chicken biryani', 'Slow-cooked chicken, fragrant basmati and our house spice blend.', 'Biryani', 29900, False, 'Milk', 15),
            ('Hyderabadi mutton biryani', 'Tender mutton layered with saffron rice, sealed and cooked on dum.', 'Biryani', 39900, False, 'Milk', 20),
            ('Paneer dum biryani', 'Spiced paneer, caramelised onions and long-grain basmati.', 'Biryani', 26900, True, 'Milk, nuts', 12),
            ('Chicken 65', 'Crisp chicken tossed with curry leaves, chilli and garlic.', 'Sides', 22900, False, 'Egg, wheat', 10),
            ('Mirchi ka salan', 'Green chillies in a rich sesame and peanut gravy.', 'Sides', 9900, True, 'Peanuts, sesame', 5),
            ('Double ka meetha', 'Hyderabadi bread pudding with milk, cardamom and nuts.', 'Sweets', 12900, True, 'Milk, wheat, nuts', 5),
        ]
        for index, values in enumerate(dishes, 1):
            name, description, category, price, veg, allergens, weight = values
            database.add(Dish(id=index, name=name, description=description, category=category, price=price, veg=veg, allergens=allergens, weight=weight, options={'regular': 0, 'large': 12000} if category == 'Biryani' else {'regular': 0}))
        database.flush()
        for outlet in range(1, 4):
            for dish in range(1, 7):
                database.add(Assignment(outlet_id=outlet, dish_id=dish))
        hashed = PasswordHasher().hash(os.environ.get('DEMO_PASSWORD', 'DemoPass123!'))
        for email, role, outlet, cod in [('customer@demo.test', 'customer', None, True), ('kondapur@demo.test', 'kitchen', 1, False), ('gachibowli@demo.test', 'kitchen', 2, False), ('admin@demo.test', 'admin', None, False)]:
            database.add(User(email=email, password=hashed, role=role, outlet_id=outlet, cod=cod))
        database.flush()
        sync_sequences(database)


def sync_sequences(database):
    if database.bind.dialect.name == 'postgresql':
        database.execute(text("SELECT setval(pg_get_serial_sequence('outlets', 'id'), (SELECT max(id) FROM outlets))"))
        database.execute(text("SELECT setval(pg_get_serial_sequence('dishes', 'id'), (SELECT max(id) FROM dishes))"))


if __name__ == '__main__':
    seed()
