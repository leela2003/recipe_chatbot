# quantity_generator.py
from random import randint, choice

def generate_quantities(ingredients: list):
    """
    Takes a list of ingredients (e.g. ["egg", "onion", "tomato"])
    and returns realistic quantity descriptions.
    """

    units = ["cup", "cups", "tbsp", "tsp", "pieces", "g", "ml"]
    result = []

    for ing in ingredients:
        num = randint(1, 4)
        unit = choice(units)
        result.append(f"{num} {unit} {ing}")

    return ", ".join(result)
