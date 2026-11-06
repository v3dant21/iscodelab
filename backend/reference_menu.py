"""Readable items transcribed from the four user-supplied menu photos.

Prices are INR. Existing six demo dishes are retained. Cropped, ambiguous or
repeated entries are omitted; spelling is normalized for display. Descriptions
are editorial category labels, not verified recipes. Allergens are unverified.
Run explicitly to extend an existing demo: python reference_menu.py.
"""
from sqlalchemy import select
from models import Assignment, Dish, Outlet, SessionLocal

# category, vegetarian default, menu lines (name | rupees)
SECTIONS = [
('Biryani', True, '''Biryani Rice|279
Veg Biryani|289
Mushroom Biryani|319
Kaju Biryani|439'''),
('Biryani', False, '''Egg Biryani|339
Nizam Chicken Biryani|399
Pot Biryani|419
Fry Piece Chicken Biryani|399
Special Chicken Biryani|399'''),
('Handi Biryani', False, '''Chicken Handi Biryani|519
Nizam Dum Handi Biryani|539
Fry Piece Chicken Handi Biryani|539
Special Chicken Handi Biryani|539
Natukodi Handi Biryani|599
Mutton Handi Biryani|599
Keema Handi Biryani|639'''),
('Family Packs', True, '''Veg Biryani Family Pack|639
Mushroom Biryani Family Pack|629
Paneer Biryani Family Pack|739'''),
('Family Packs', False, '''Chicken Biryani Family Pack|799
Nizam Chicken Biryani Family Pack|849
Pot Biryani Family Pack|889
Fry Piece Chicken Biryani Family Pack|889
Special Chicken Biryani Family Pack|889
Gongura Chicken Biryani Family Pack|889
Green Mirchi Chicken Biryani Family Pack|889
Avakaya Chicken Biryani Family Pack|889
Natukodi Biryani Family Pack|939
Mutton Biryani Family Pack|999
Gongura Mutton Biryani Family Pack|999
Mutton Kheema Biryani Family Pack|1039
Fish Biryani Family Pack|919
Prawns Biryani Family Pack|919'''),
('Platters', False, '''Rayalaseema Platter|1379
Non-Veg Dry Platter|1499
Tandoori Platter|1379
Tandoori Special Platter|1499'''),
('Platters', True, '''Veg Dry Platter|1299
Tandoori Veg Platter|1269'''),
('Drinks', True, '''Lassi|79
Buttermilk|75
Water Bottle|20
Cool Drinks|49'''),
('Sweets', True, '''Gulab Jamun|140
Apricot Delight|199'''),
('Chicken Kebabs', False, '''Chicken Tandoori Half|379
Chicken Tandoori Full|599
Tangdi Kebab Half|379
Tangdi Kebab Full|599
Lucknow Dum Ka Tikka Special|479
Pahadi Kebab|429
Lucknow Seekh Kebab|429
Kakori Lemon Chicken Tikka|429
Chicken Toffee Kebab|429
Chicken Reshmi Kebab|429
Chicken Sesame Kebab|429
Chicken Hariyali Kebab|429
Chicken Jaffrani Tikka|429
Chicken Kasturi Methi Tikka|429
Chicken Garlic Tikka|429
Chicken Afghani Kebab|429
Chicken Andhraki Kebab|429
Achari Chicken Tikka|429'''),
('Mutton Kebabs', False, '''Mutton Chop Tikka Kebab|489
Mutton Pudina Kebab|489
Mutton Seekh Kebab|489'''),
('Fish Kebabs', False, '''Fish Achari Tikka|449
Fish Hariyali Tikka|449
Fish Tikka|449
Lasooni Fish Tikka|449
Lemon Fish Tikka|449
Pudina Fish Tikka|449'''),
('Breads', True, '''Phulka|25
Ghee Phulka|29
Chapati|29
Kadak Jowar Roti|35
Tandoori Roti|52
Butter Roti|59
Plain Naan|59
Butter Naan|69
Garlic Naan|79
Cheese Naan|79
Plain Paratha|59
Lachha Paratha|69
Gobi Paratha|69
Methi Paratha|79
Paneer Paratha|89
Pudina Paratha|79
Aloo Paratha|79
Plain Kulcha|59
Masala Kulcha|79
Paneer Kulcha|89
Roti Basket|319'''),
('Breads', False, '''Keema Naan|155'''),
('Rayalaseema Specials', True, '''Ragi Mudda|149
Jowar Roti|29
Gutti Vankaya|219
Pappu|99
Gongura Pappu|119
Aloo Fry|209
Bendakaya Fry|209
Rasam|79
Sambar|89
Curd|79'''),
('Rayalaseema Specials', False, '''Natukodi Pulusu|409
Talakaya Mamsam|369
Paya|369
Roti Paya|419
Puri Mutton|449
Roti Natukodi Pulusu|419'''),
('Veg Soups', True, '''Tomato Soup|159
Veg Cantonese Soup|159
Lemon Coriander Soup|159
Veg Clear Soup|159
Veg Corn Soup|159
Veg Hot and Sour Soup|159
Veg Manchow Soup|159
Veg Noodles Soup|159
Miriyala Charu|159'''),
('Non-Veg Soups', False, '''Mutton Bone Soup|219
Paya Soup|219
Chicken Cantonese Soup|169
Chicken Clear Soup|169
Chicken Corn Soup|169
Chicken Hot and Sour Soup|169
Chicken Manchow Soup|169'''),
('Veg Starters', True, '''Gobi Chilli|309
Gobi 65|309
Ginger Gobi|309
Gobi Manchurian|309
Ginger Veg|309
Veg Manchurian|309
Veg 65|309
Paneer 65|339
Paneer Manchurian|339
Paneer Bhurji|339
Chilli Paneer|339
Aloo 65|289
Babycorn Manchurian|309
Babycorn Chilli|309
Kaju Fry|369
Green Peas Roast|309'''),
('Fish Starters', False, '''Garlic Fish Roast|439
Apollo Fish|439
Fish 65|439
Fish Manchurian|439
Prawns 65|439
Loose Prawns|439
Garlic Fish Fry|439
Crispy Fish|439'''),
('Veg Curries', True, '''Veg Malai Kofta|299
Veg Paneer Kofta|319
Paneer Butter Masala|319
Veg Mix Curry|299
Veg Shahi Kurma|309
Paneer Shahi Kurma|319
Palak Paneer|319
Aloo Palak|299
Kadai Paneer|319
Kadai Veg|299
Plain Palak|299
Kaju Curry|299
Mushroom Curry|299
Tomato Curry|299
Green Peas Masala|299
Dal Fry|269'''),
('Chicken Curries', False, '''Andhra Chicken Curry (Bone-in)|369
Andhra Chicken Curry (Boneless)|379
Chicken Masala (Bone-in)|379
Hariyali Chicken Curry|379
Hyderabadi Chicken Curry|379
Kadai Chicken|379
Butter Chicken|379
Chicken Mughlai|379
Palak Chicken|379
Chicken Kolhapuri|379
Methi Chicken|379
Rayalaseema Chicken|379
Gongura Chicken|379'''),
('Mutton Curries', False, '''Mutton Pulusu|439
Gongura Mutton|439
Rayalaseema Mutton|439'''),
('Rice', True, '''Ghee Rice|279
Jeera Rice|279
Veg Fried Rice|279
Steamed Rice|75
Sambar Rice|189
Curd Rice|185'''),
('Rice', False, '''Egg Fried Rice|299
Chicken Fried Rice|359
Mutton Fried Rice|409
Mixed Fried Rice|409'''),
('Egg Dishes', False, '''Egg Curry|229
Egg Masala|229
Egg Bhurji|209
Egg Fry|189
Egg Omelette|159
Boiled Eggs|99
Egg Chilli|269
Egg 65|269'''),
]


def extend_menu(database):
    """Add missing reference dishes/assignments, preserving staff prices and stock."""
    from curated_menu import SELECTED
    outlets = list(database.scalars(select(Outlet)))
    added = 0
    for category, veg, rows in SECTIONS:
        for row in rows.splitlines():
            name, price = row.split('|')
            if name not in SELECTED:
                continue
            dish = database.scalar(select(Dish).where(Dish.name == name))
            if dish is None:
                portion = 'family pack' if category == 'Family Packs' else 'handi (2 people)' if category == 'Handi Biryani' else 'half' if name.endswith(' Half') else 'full' if name.endswith(' Full') else 'regular'
                description = f'{name}, from our {category.lower()} selection.'
                if category == 'Handi Biryani':
                    description = f'{name}, a handi portion for two.'
                dish = Dish(name=name, description=description, category=category, price=int(price) * 100, veg=veg,
                            allergens='Not verified — please check with the kitchen before ordering.',
                            weight=15 if 'Biryani' in category or category == 'Family Packs' else 5,
                            options={portion: 0})
                database.add(dish)
                database.flush()
                added += 1
            for outlet in outlets:
                if database.get(Assignment, (outlet.id, dish.id)) is None:
                    database.add(Assignment(outlet_id=outlet.id, dish_id=dish.id))
    return added


if __name__ == '__main__':
    with SessionLocal.begin() as database:
        print(f'Added {extend_menu(database)} reference dishes.')
