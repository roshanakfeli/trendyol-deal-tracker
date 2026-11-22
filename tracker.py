
import json
import os
import urllib.parse
import urllib.request
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


def build_message(deals):
    lines = [
        "🛍️ Trendyol Deal Tracker",
        "📢 گزارش آزمایشی تخفیف‌ها",
        ""
    ]

    if not deals:
        lines.append("هیچ محصول مناسبی پیدا نشد.")
        return "\n".join(lines)

    for index, product in enumerate(deals, start=1):
        lines.extend([
            f"{index}. {product['name']}",
            f"🏷️ برند: {product['brand']}",
            f"💰 قیمت: {product['current_price']} TRY",
            f"🔥 تخفیف: {product['discount']}%",
            f"📏 سایز: {product['size'] or 'بدون سایز'}",
            f"🔗 لینک: {product['url']}",
            ""
        ])

    return "\n".join(lines)


def send_telegram_message(message):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message
    }).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)

    if not result.get("ok"):
        raise RuntimeError("Telegram message failed")

    print("Telegram message sent successfully!")


def main():
    products = load_products()
    deals = find_best_deals(products)

    print(f"Found {len(deals)} matching deals")

    message = build_message(deals)
    send_telegram_message(message)


if __name__ == "__main__":
    main()
