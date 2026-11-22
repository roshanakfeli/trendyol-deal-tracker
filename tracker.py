
import json
from pathlib import Path

MIN_DISCOUNT = 30
SHOE_CATEGORIES = {"boots", "shoes"}
ALLOWED_SHOE_SIZES = {"38.5", "39"}


def load_products():
    file_path = Path(__file__).with_name("products.json")

    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def calculate_discount(original_price, current_price):
    if original_price <= 0:
        return 0

    return (original_price - current_price) / original_price * 100


def find_best_deals(products):
    deals = []

    for product in products:
        original_price = product["original_price"]
        current_price = product["current_price"]

        discount = calculate_discount(original_price, current_price)

        if discount < MIN_DISCOUNT:
            continue

        if product["category"] in SHOE_CATEGORIES:
            if str(product["size"]) not in ALLOWED_SHOE_SIZES:
                continue

        deals.append({
            **product,
            "discount": round(discount, 1)
        })

    return sorted(deals, key=lambda item: item["current_price"])


def main():
    products = load_products()
    deals = find_best_deals(products)

    print(f"Found {len(deals)} matching deals:\n")

    for product in deals:
        print(f"Product: {product['name']}")
        print(f"Brand: {product['brand']}")
        print(f"Price: {product['current_price']} TRY")
        print(f"Discount: {product['discount']}%")
        print(f"Size: {product['size']}")
        print(f"Link: {product['url']}")
        print("-" * 40)


if __name__ == "__main__":
    main()
