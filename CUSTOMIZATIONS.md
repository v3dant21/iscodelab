# Dish customization catalogue

Reviewed 7 November 2026. Applies to the curated 70-item Dum & Dastaan menu.

## Research and scope

These are proposed preparation preferences adapted for this app, not a claim that the photographed restaurant or every outlet offers them. Kitchen operators must validate feasibility, ingredients, packaging and availability before live fulfilment. Source prices are not copied. Existing dish/portion prices and the existing ₹30 extra-raita price remain unchanged; preparation preferences have no added charge. No new ice-cream upsell or protein substitution is invented.

Restaurant menu evidence:

- [Biryani By Kilo](https://biryanibykilo.com/): biryani portions, burani raita and salan. Basis for biryani accompaniment controls; less/extra serving masala and onion omission are app-specific preparation proposals, not quoted vendor customizations.
- [House of Kebabs](https://www.hbkhouston.com/menu): mild, medium and spicy preferences. Basis for curry and freshly tossed starter/rice preferences. Pre-made sauce and marinade caveats remain visible.
- [Sanskruti Manchester menu](https://www.sanskrutirestaurant.co.uk/manchester/wp-content/uploads/2024/07/Sanskrutibacklit.pdf): dry or gravy vegetable Manchurian.
- [Malabar Plate menu](https://malabarplate.com/wp-content/uploads/2023/08/Malabar-Plate-Menu.pdf): dry/gravy Manchurian and chilli preparations. Applied to the app's Veg Manchurian, Chilli Paneer and Babycorn Chilli.
- [Minerva Blue Fox menu](https://minervahotels.in/wp-content/uploads/2023/10/BF-Final-menu-22-11-2021-1.pdf): sweet/salt lassi, masala buttermilk, Gulab Jamun, Double Ka Meetha and Khubaani dessert variations. No added sugar/ice and separate garnish/cream are app-specific preparation preferences. Ice cream appears in the source but is not added here without an approved price and stock model.
- [Dosa Grill](https://dosagrill.com/menu-design/): plain, butter, garlic/chilli breads and sweet/salted lassi. Bread cuts and reduced finishing butter/garlic are adapted preparation requests; no recipe-level dairy-free claim.
- [Sizzle and Spice](https://www.sizzleandspiceindiancuisine.com/menu?location=Restaurant&menu=menu): grilled kebabs with mint/yoghurt accompaniments; basis for chutney/onion side preferences.
- [Belmond lounge menu](https://pdfs.belmond.com/MNH-Lounge-Lunch-Menu.pdf): tomato soup with cream and croutons. Finish/crouton omission is adapted as a preparation preference.

For the remaining rice, lemon coriander soup and omelette dishes, herb/pepper/lemon/chilli choices are culinary preparation proposals. They are deliberately labelled as finishes or garnishes, not verified recipe substitutions. Curry names, protein types, family/handi servings and prices remain the original catalogue's choices.

## Behaviour

`backend/customizations.py` owns the catalogue and validates selection IDs. Both catalog and outlet-menu responses publish the same profiles. Unknown/admin-created dishes get no guessed profile. Missing selections from old carts resolve to house defaults; unknown groups or values are rejected. The server supplies readable labels and recomputes the full line price.

Selections distinguish cart variants, survive refresh, can be edited in the bag, and are shown in checkout review, order tracking, kitchen tickets and HTML/PDF invoice snapshots. Historical invoice snapshots are not rewritten. Raita is supported for biryani, including handi and family-pack dishes, and rejected for other dishes. Paid extras are never preselected.

Allergen statements remain in place. Removing a garnish or finishing cream does not remove ingredients already in a sauce, marinade, dough or dessert, and no allergy-safe promise is made. Phone/email/order permissions remain unchanged.

## Per-dish coverage

The following table is generated from the current curated catalogue. It is an implementation inventory; the research/assumption distinction above applies throughout.

| Dish | Choices |
|---|---|
| Achari Chicken Tikka | Mint chutney: On the side, No chutney; Onion garnish: On the side, No onion garnish |
| Andhra Chicken Curry (Bone-in) | Spice preference: House spice, Milder, Extra hot; Fresh coriander garnish: As prepared, No fresh coriander |
| Andhra Chicken Curry (Boneless) | Spice preference: House spice, Milder, Extra hot; Fresh coriander garnish: As prepared, No fresh coriander |
| Apollo Fish | Spice preference: House spice, Milder, Extra hot; Lemon wedge: On the side, No lemon wedge |
| Apricot Delight | Nut garnish: As prepared, Pack separately, No added nut garnish; Cream topping: As prepared, Pack separately, No added cream |
| Babycorn Chilli | Sauce style: Dry toss, With gravy; Spice preference: House spice, Milder, Extra hot |
| Butter Chicken | Spice preference: House spice, Milder, Extra hot; Cream finish: As prepared, No added cream |
| Butter Naan | Butter finish: As prepared, Light butter, No butter brushed on; Bread cut: Whole, Cut in half |
| Buttermilk | Buttermilk style: Masala, Plain salted; Fresh green chilli: As prepared, No added green chilli |
| Chapati | Bread cut: Whole, Cut in half |
| Chicken 65 | Spice preference: House spice, Milder, Extra hot; Lemon wedge: On the side, No lemon wedge |
| Chicken Biryani Family Pack | Biryani masala: House mix, Less masala, Extra masala; Fried onion topping: As prepared, No added fried onion |
| Chicken Fried Rice | Spice preference: House spice, Milder, Extra hot; Spring onion garnish: As prepared, No spring onion garnish |
| Chicken Garlic Tikka | Mint chutney: On the side, No chutney; Onion garnish: On the side, No onion garnish |
| Chicken Handi Biryani | Biryani masala: House mix, Less masala, Extra masala; Fried onion topping: As prepared, No added fried onion |
| Chicken Reshmi Kebab | Mint chutney: On the side, No chutney; Onion garnish: On the side, No onion garnish |
| Chicken Tandoori Full | Mint chutney: On the side, No chutney; Onion garnish: On the side, No onion garnish |
| Chicken Tandoori Half | Mint chutney: On the side, No chutney; Onion garnish: On the side, No onion garnish |
| Chilli Paneer | Sauce style: Dry toss, With gravy; Spice preference: House spice, Milder, Extra hot |
| Curd Rice | Fresh green chilli: As prepared, No added green chilli; Fresh coriander garnish: As prepared, No fresh coriander |
| Dal Fry | Spice preference: House spice, Milder, Extra hot; Fresh coriander garnish: As prepared, No fresh coriander |
| Double ka meetha | Nut garnish: As prepared, Pack separately, No added nut garnish; Serving preference: Packed warm, Room temperature |
| Dum chicken biryani | Biryani masala: House mix, Less masala, Extra masala; Fried onion topping: As prepared, No added fried onion |
| Egg Biryani | Biryani masala: House mix, Less masala, Extra masala; Fried onion topping: As prepared, No added fried onion |
| Egg Curry | Spice preference: House spice, Milder, Extra hot; Fresh coriander garnish: As prepared, No fresh coriander |
| Egg Fried Rice | Spice preference: House spice, Milder, Extra hot; Spring onion garnish: As prepared, No spring onion garnish |
| Egg Omelette | Omelette style: Onion masala, Plain; Fresh green chilli: As prepared, No added green chilli |
| Fish Tikka | Mint chutney: On the side, No chutney; Onion garnish: On the side, No onion garnish |
| Fry Piece Chicken Biryani | Biryani masala: House mix, Less masala, Extra masala; Fried onion topping: As prepared, No added fried onion |
| Garlic Naan | Butter finish: As prepared, Light butter, No butter brushed on; Bread cut: Whole, Cut in half; Garlic topping: Regular garlic, Light garlic |
| Gobi 65 | Spice preference: House spice, Milder, Extra hot; Lemon wedge: On the side, No lemon wedge |
| Gongura Chicken | Spice preference: House spice, Milder, Extra hot; Fresh coriander garnish: As prepared, No fresh coriander |
| Gongura Mutton | Spice preference: House spice, Milder, Extra hot; Fresh coriander garnish: As prepared, No fresh coriander |
| Gulab Jamun | Sugar syrup: Regular syrup, Less syrup; Serving preference: Packed warm, Room temperature |
| Hyderabadi mutton biryani | Biryani masala: House mix, Less masala, Extra masala; Fried onion topping: As prepared, No added fried onion |
| Jeera Rice | Fresh coriander garnish: As prepared, No fresh coriander; Ghee finish: As prepared, No added ghee |
| Kadai Chicken | Spice preference: House spice, Milder, Extra hot; Fresh coriander garnish: As prepared, No fresh coriander |
| Kadai Paneer | Spice preference: House spice, Milder, Extra hot; Fresh coriander garnish: As prepared, No fresh coriander |
| Kaju Biryani | Biryani masala: House mix, Less masala, Extra masala; Fried onion topping: As prepared, No added fried onion |
| Lachha Paratha | Butter finish: As prepared, Light butter, No butter brushed on; Bread cut: Whole, Cut in half |
| Lassi | Lassi style: Sweet, Salted, No added sugar; Ice: Chilled, no ice, With ice |
| Lemon Coriander Soup | Lemon finish: House balance, Light lemon; Pepper: Regular, Light pepper |
| Lemon Fish Tikka | Mint chutney: On the side, No chutney; Onion garnish: On the side, No onion garnish |
| Mirchi ka salan | Whole chillies: Include chillies, Gravy only; Fresh coriander garnish: As prepared, No fresh coriander |
| Mushroom Biryani | Biryani masala: House mix, Less masala, Extra masala; Fried onion topping: As prepared, No added fried onion |
| Mushroom Curry | Spice preference: House spice, Milder, Extra hot; Fresh coriander garnish: As prepared, No fresh coriander |
| Mutton Biryani Family Pack | Biryani masala: House mix, Less masala, Extra masala; Fried onion topping: As prepared, No added fried onion |
| Mutton Chop Tikka Kebab | Mint chutney: On the side, No chutney; Onion garnish: On the side, No onion garnish |
| Mutton Handi Biryani | Biryani masala: House mix, Less masala, Extra masala; Fried onion topping: As prepared, No added fried onion |
| Mutton Pulusu | Spice preference: House spice, Milder, Extra hot; Fresh coriander garnish: As prepared, No fresh coriander |
| Mutton Seekh Kebab | Mint chutney: On the side, No chutney; Onion garnish: On the side, No onion garnish |
| Nizam Chicken Biryani | Biryani masala: House mix, Less masala, Extra masala; Fried onion topping: As prepared, No added fried onion |
| Palak Paneer | Spice preference: House spice, Milder, Extra hot; Cream finish: As prepared, No added cream |
| Paneer 65 | Spice preference: House spice, Milder, Extra hot; Lemon wedge: On the side, No lemon wedge |
| Paneer Biryani Family Pack | Biryani masala: House mix, Less masala, Extra masala; Fried onion topping: As prepared, No added fried onion |
| Paneer Butter Masala | Spice preference: House spice, Milder, Extra hot; Cream finish: As prepared, No added cream |
| Paneer Kulcha | Butter finish: As prepared, Light butter, No butter brushed on; Bread cut: Whole, Cut in half; Fresh green chilli: As prepared, No added green chilli |
| Paneer dum biryani | Biryani masala: House mix, Less masala, Extra masala; Fried onion topping: As prepared, No added fried onion |
| Plain Naan | Bread cut: Whole, Cut in half |
| Pot Biryani | Biryani masala: House mix, Less masala, Extra masala; Fried onion topping: As prepared, No added fried onion |
| Prawns 65 | Spice preference: House spice, Milder, Extra hot; Lemon wedge: On the side, No lemon wedge |
| Prawns Biryani Family Pack | Biryani masala: House mix, Less masala, Extra masala; Fried onion topping: As prepared, No added fried onion |
| Tandoori Roti | Bread cut: Whole, Cut in half |
| Tangdi Kebab Half | Mint chutney: On the side, No chutney; Onion garnish: On the side, No onion garnish |
| Tomato Soup | Croutons: Pack separately, No croutons; Cream finish: As prepared, No added cream |
| Veg Biryani | Biryani masala: House mix, Less masala, Extra masala; Fried onion topping: As prepared, No added fried onion |
| Veg Biryani Family Pack | Biryani masala: House mix, Less masala, Extra masala; Fried onion topping: As prepared, No added fried onion |
| Veg Fried Rice | Spice preference: House spice, Milder, Extra hot; Spring onion garnish: As prepared, No spring onion garnish |
| Veg Malai Kofta | Spice preference: House spice, Milder, Extra hot; Cream finish: As prepared, No added cream |
| Veg Manchurian | Sauce style: Dry toss, With gravy; Spice preference: House spice, Milder, Extra hot |
