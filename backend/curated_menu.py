"""Editorial 70-dish selection: 35 vegetarian and 35 non-vegetarian.

This is a balanced shortlist, not a sales ranking. Hidden dishes and historical
orders remain in the database. Re-run explicitly to apply the shortlist.
"""
from sqlalchemy import select
from models import Assignment, Dish, SessionLocal

VEG = '''Paneer dum biryani
Mirchi ka salan
Double ka meetha
Veg Biryani
Mushroom Biryani
Kaju Biryani
Paneer Biryani Family Pack
Veg Biryani Family Pack
Gobi 65
Chilli Paneer
Paneer 65
Veg Manchurian
Babycorn Chilli
Paneer Butter Masala
Palak Paneer
Kadai Paneer
Dal Fry
Mushroom Curry
Veg Malai Kofta
Garlic Naan
Butter Naan
Plain Naan
Tandoori Roti
Chapati
Lachha Paratha
Paneer Kulcha
Veg Fried Rice
Jeera Rice
Curd Rice
Tomato Soup
Lemon Coriander Soup
Lassi
Buttermilk
Gulab Jamun
Apricot Delight'''.splitlines()
NON_VEG = '''Dum chicken biryani
Hyderabadi mutton biryani
Chicken 65
Egg Biryani
Nizam Chicken Biryani
Pot Biryani
Fry Piece Chicken Biryani
Chicken Handi Biryani
Mutton Handi Biryani
Chicken Biryani Family Pack
Mutton Biryani Family Pack
Prawns Biryani Family Pack
Chicken Tandoori Half
Chicken Tandoori Full
Tangdi Kebab Half
Chicken Reshmi Kebab
Chicken Garlic Tikka
Achari Chicken Tikka
Mutton Chop Tikka Kebab
Mutton Seekh Kebab
Apollo Fish
Prawns 65
Fish Tikka
Lemon Fish Tikka
Andhra Chicken Curry (Bone-in)
Andhra Chicken Curry (Boneless)
Butter Chicken
Kadai Chicken
Gongura Chicken
Mutton Pulusu
Gongura Mutton
Chicken Fried Rice
Egg Fried Rice
Egg Curry
Egg Omelette'''.splitlines()
SELECTED = frozenset(VEG + NON_VEG)
assert len(VEG) == len(NON_VEG) == 35 and len(SELECTED) == 70


def curate(database):
    from reference_menu import extend_menu
    extend_menu(database)
    dishes = {dish.id: dish for dish in database.scalars(select(Dish))}
    assert SELECTED.issubset({dish.name for dish in dishes.values()}), 'Missing selected dishes'
    for assignment in database.scalars(select(Assignment)):
        assignment.enabled = dishes[assignment.dish_id].name in SELECTED
    return len(SELECTED)


if __name__ == '__main__':
    with SessionLocal.begin() as database:
        print(f'Published {curate(database)} selected dishes (35 veg / 35 non-veg).')
