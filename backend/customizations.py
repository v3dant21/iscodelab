"""Dish-specific preparation choices. Research and kitchen assumptions: CUSTOMIZATIONS.md.

Prices remain unchanged for preparation preferences. Portion prices are owned by
Dish.options; extra raita retains the existing charge. Never infer allergen removal.
"""
from copy import deepcopy


def group(id, label, *choices, note=''):
    return {'id': id, 'label': label, 'default': choices[0][0],
            'choices': [{'id': key, 'label': text} for key, text in choices], 'note': note}


SPICE = group('spice', 'Spice preference', ('regular', 'House spice'), ('mild', 'Milder'), ('hot', 'Extra hot'), note='Base sauces and marinades already contain spices; milder is not spice-free.')
HERBS = group('herbs', 'Fresh coriander garnish', ('usual', 'As prepared'), ('none', 'No fresh coriander'))
ONION = group('onion', 'Onion garnish', ('usual', 'On the side'), ('none', 'No onion garnish'), note='This changes the garnish only, not onion in the recipe.')
CHUTNEY = group('chutney', 'Mint chutney', ('side', 'On the side'), ('none', 'No chutney'))
FINISH = group('butter', 'Butter finish', ('usual', 'As prepared'), ('light', 'Light butter'), ('none', 'No butter brushed on'), note='Bread dough may still contain milk or butter.')
CUT = group('cut', 'Bread cut', ('whole', 'Whole'), ('halves', 'Cut in half'))
NUTS = group('garnish', 'Nut garnish', ('usual', 'As prepared'), ('separate', 'Pack separately'), ('none', 'No added nut garnish'), note='Nuts may already be in the dessert. This is not a nut-free option.')
CHILLI = group('chilli', 'Fresh green chilli', ('usual', 'As prepared'), ('none', 'No added green chilli'))


def customization_groups(dish):
    name = dish.name.lower()
    if 'biryani' in name:
        groups = [group('masala', 'Biryani masala', ('usual', 'House mix'), ('less', 'Less masala'), ('extra', 'Extra masala'), note='Mixed while serving; dum-cooked rice and meat retain their original seasoning.'),
                  group('fried_onion', 'Fried onion topping', ('usual', 'As prepared'), ('none', 'No added fried onion'))]
    elif name == 'lassi':
        groups = [group('flavour', 'Lassi style', ('sweet', 'Sweet'), ('salted', 'Salted'), ('unsweetened', 'No added sugar')),
                  group('ice', 'Ice', ('none', 'Chilled, no ice'), ('ice', 'With ice'))]
    elif name == 'buttermilk':
        groups = [group('style', 'Buttermilk style', ('masala', 'Masala'), ('plain', 'Plain salted')), CHILLI]
    elif name in ('gulab jamun', 'double ka meetha', 'apricot delight'):
        groups = ([group('syrup', 'Sugar syrup', ('usual', 'Regular syrup'), ('less', 'Less syrup'), note='The jamun is already soaked in syrup; this is not a low-sugar option.')] if name == 'gulab jamun' else [NUTS])
        groups += ([group('temperature', 'Serving preference', ('warm', 'Packed warm'), ('room', 'Room temperature'))] if name != 'apricot delight' else [group('cream', 'Cream topping', ('usual', 'As prepared'), ('separate', 'Pack separately'), ('none', 'No added cream'), note='The dessert base still contains dairy.')])
    elif any(word in name for word in ('naan', 'roti', 'chapati', 'paratha', 'kulcha')):
        groups = [CUT]
        if name not in ('plain naan', 'tandoori roti', 'chapati'):
            groups.insert(0, FINISH)
        if name == 'garlic naan':
            groups.append(group('garlic', 'Garlic topping', ('usual', 'Regular garlic'), ('light', 'Light garlic')))
        if name == 'paneer kulcha':
            groups.append(CHILLI)
    elif name == 'tomato soup':
        groups = [group('croutons', 'Croutons', ('side', 'Pack separately'), ('none', 'No croutons')),
                  group('cream', 'Cream finish', ('usual', 'As prepared'), ('none', 'No added cream'), note='The soup base may still contain dairy.')]
    elif name == 'lemon coriander soup':
        groups = [group('lemon', 'Lemon finish', ('usual', 'House balance'), ('light', 'Light lemon')), group('pepper', 'Pepper', ('usual', 'Regular'), ('light', 'Light pepper'))]
    elif name == 'curd rice':
        groups = [CHILLI, HERBS]
    elif name == 'jeera rice':
        groups = [HERBS, group('ghee', 'Ghee finish', ('usual', 'As prepared'), ('none', 'No added ghee'), note='This changes the finish only, not the cooking fat.')]
    elif 'fried rice' in name:
        groups = [SPICE, group('spring_onion', 'Spring onion garnish', ('usual', 'As prepared'), ('none', 'No spring onion garnish'))]
    elif name == 'egg omelette':
        groups = [group('style', 'Omelette style', ('masala', 'Onion masala'), ('plain', 'Plain')), CHILLI]
    elif name in ('veg manchurian', 'chilli paneer', 'babycorn chilli'):
        groups = [group('style', 'Sauce style', ('dry', 'Dry toss'), ('gravy', 'With gravy')), SPICE]
    elif any(word in name for word in ('kebab', 'tikka', 'tandoori')):
        groups = [CHUTNEY, ONION]
    elif name.endswith('65') or name == 'apollo fish':
        groups = [SPICE, group('lemon', 'Lemon wedge', ('side', 'On the side'), ('none', 'No lemon wedge'))]
    elif name == 'mirchi ka salan':
        groups = [group('chillies', 'Whole chillies', ('usual', 'Include chillies'), ('gravy', 'Gravy only'), note='The gravy is cooked with chillies, peanuts and sesame.'), HERBS]
    elif 'curr' in dish.category.lower() or name in ('egg curry', 'dal fry'):
        groups = [SPICE, HERBS]
        if name in ('butter chicken', 'paneer butter masala', 'veg malai kofta', 'palak paneer'):
            groups[1] = group('cream', 'Cream finish', ('usual', 'As prepared'), ('none', 'No added cream'), note='The base sauce still contains dairy.')
    else:
        groups = []  # Unknown/admin-created dishes must not acquire guessed options.
    return deepcopy(groups)


def supports_raita(dish):
    return 'biryani' in dish.name.lower()


def resolve_choices(dish, selections):
    groups = customization_groups(dish)
    if set(selections) - {g['id'] for g in groups}:
        raise ValueError('An option is not available for this dish. Refresh the menu and choose again.')
    resolved, labels = {}, []
    for g in groups:
        value = selections.get(g['id'], g['default'])
        choice = next((c for c in g['choices'] if c['id'] == value), None)
        if choice is None:
            raise ValueError('A customization is no longer available. Refresh the menu and choose again.')
        resolved[g['id']] = value
        labels.append(f"{g['label']}: {choice['label']}")
    return resolved, labels
