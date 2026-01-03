"""
generate_data.py - Generates 4 test data files according to requirements

Requirements:
1. data1.json: All records match both filter conditions (quantity >= 20 AND price >= 2.0)
2. data2.json: All records fail filter1 (quantity < 20), but some pass filter2 (price >= 2.0) - Results: 0 records
3. data3.json: All records fail filter2 (price < 2.0), but some pass filter1 (quantity >= 20) - Results: 0 records
4. data4.json: Some records match both filters - Results: partial
"""

import json
import random

random.seed(42)

# Food name prefixes
FOOD_TYPES = [
    "MILK", "BREAD", "COFFEE", "BUTTER", "CHEESE", "EGGS", "YOGURT",
    "CHICKEN", "BEEF", "PORK", "FISH", "RICE", "PASTA", "FLOUR",
    "SUGAR", "SALT", "PEPPER", "OIL", "JUICE", "WATER", "SODA",
    "TEA", "COCOA", "CEREAL", "OATS", "HONEY", "JAM", "SAUCE",
    "KETCHUP", "MUSTARD", "MAYO", "CREAM", "WINE", "BEER", "CIDER",
    "APPLE", "BANANA", "ORANGE", "GRAPE", "MELON", "BERRY", "PEACH",
    "CARROT", "POTATO", "ONION", "GARLIC", "TOMATO", "LETTUCE", "CABBAGE"
]


def generate_data1():
    """All records match both filters: quantity >= 20 AND price >= 2.0"""
    foods = []
    for i in range(300):
        food_type = random.choice(FOOD_TYPES)
        item = {
            "name": f"{food_type}-{1000 + i:04d}",
            "quantity": random.randint(20, 200),  # >= 20
            "price": round(random.uniform(2.0, 15.0), 2)  # >= 2.0
        }
        foods.append(item)

    with open('data1.json', 'w') as f:
        json.dump({"foods": foods}, f, indent=2)

    print(f"Generated data1.json: {len(foods)} items (all match both filters)")


def generate_data2():
    """All records fail filter1 (quantity < 20), but some pass filter2 (price >= 2.0)
    Result: 0 records (because both filters must pass)"""
    foods = []
    for i in range(300):
        food_type = random.choice(FOOD_TYPES)
        # Ensure some pass filter2 but all fail filter1
        if i < 200:
            price = round(random.uniform(2.0, 15.0), 2)  # Pass filter2
        else:
            price = round(random.uniform(0.5, 1.99), 2)  # Fail filter2

        item = {
            "name": f"{food_type}-{2000 + i:04d}",
            "quantity": random.randint(1, 19),  # < 20 (fail filter1)
            "price": price
        }
        foods.append(item)

    with open('data2.json', 'w') as f:
        json.dump({"foods": foods}, f, indent=2)

    pass_filter2 = sum(1 for item in foods if item['price'] >= 2.0)
    print(f"Generated data2.json: {len(foods)} items (0 match both filters)")
    print(f"  - All fail filter1 (quantity < 20)")
    print(f"  - {pass_filter2} pass filter2 (price >= 2.0)")


def generate_data3():
    """All records fail filter2 (price < 2.0), but some pass filter1 (quantity >= 20)
    Result: 0 records (because both filters must pass)"""
    foods = []
    for i in range(300):
        food_type = random.choice(FOOD_TYPES)
        # Ensure some pass filter1 but all fail filter2
        if i < 200:
            quantity = random.randint(20, 200)  # Pass filter1
        else:
            quantity = random.randint(1, 19)  # Fail filter1

        item = {
            "name": f"{food_type}-{3000 + i:04d}",
            "quantity": quantity,
            "price": round(random.uniform(0.5, 1.99), 2)  # < 2.0 (fail filter2)
        }
        foods.append(item)

    with open('data3.json', 'w') as f:
        json.dump({"foods": foods}, f, indent=2)

    pass_filter1 = sum(1 for item in foods if item['quantity'] >= 20)
    print(f"Generated data3.json: {len(foods)} items (0 match both filters)")
    print(f"  - {pass_filter1} pass filter1 (quantity >= 20)")
    print(f"  - All fail filter2 (price < 2.0)")


def generate_data4():
    """Some records match both filters (partial results)"""
    foods = []
    for i in range(300):
        food_type = random.choice(FOOD_TYPES)

        # Create different categories
        if i < 100:
            # Pass both filters
            quantity = random.randint(20, 200)
            price = round(random.uniform(2.0, 15.0), 2)
        elif i < 200:
            # Fail filter1
            quantity = random.randint(1, 19)
            price = round(random.uniform(2.0, 15.0), 2)
        else:
            # Fail filter2
            quantity = random.randint(20, 200)
            price = round(random.uniform(0.5, 1.99), 2)

        item = {
            "name": f"{food_type}-{4000 + i:04d}",
            "quantity": quantity,
            "price": price
        }
        foods.append(item)

    with open('data4.json', 'w') as f:
        json.dump({"foods": foods}, f, indent=2)

    pass_both = sum(1 for item in foods if item['quantity'] >= 20 and item['price'] >= 2.0)
    print(f"Generated data4.json: {len(foods)} items ({pass_both} match both filters)")


if __name__ == "__main__":
    print("Generating data files...")
    print("\nFilters:")
    print("  Filter 1: quantity >= 20")
    print("  Filter 2: price >= 2.0")
    print("\n" + "="*60)

    generate_data1()
    print()
    generate_data2()
    print()
    generate_data3()
    print()
    generate_data4()

    print("\n" + "="*60)
    print("All data files generated successfully!")
    print("\nTo test:")
    print("  1. First compile C++: g++ -o main main.cpp -lOpenCL -lpthread")
    print("  2. Run C++: ./main data1.json")
    print("  3. In another terminal, run Python: python3 worker.py")