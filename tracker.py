
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

MIN_DISCOUNT = 30
ALLOWED_SHOE_SIZES = {"38.5", "39"}

BASE_URL = "https://www.trendyol.com"


def load_product():
    file_path = Path(__file__).with_name("sample_product.json")

    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def calculate_discount(original_price, final_price):
    if original_price <= 0:
        return 0

    return round(
        (original_price - final_price) / original_price * 100,
        1
    )


def analyze_product(product):
    price = product["price"]
    final_price = price["discountedPrice"]

    # Promotional reference price
    reference_price = product["recommendedRetailPrice"][
        "sellingPriceNumerized"
    ]

    discount = calculate_discount(reference_price, final_price)

    size = str(product.get("variantValue", ""))
    is_sold_out = product.get("tagStockBar", {}).get(
        "isSoldOut", False
    )

    category_id = product.get("category", {}).get("id")
    shoe_category_ids = {408}

    if category_id in shoe_category_ids:
        if size not in ALLOWED_SHOE_SIZES:
            return None

    if is_sold_out:
        return None

    if discount < MIN_DISCOUNT:
        return None

    product_url = BASE_URL + product["url"]

    return {
        "id": product["id"],
        "name": product["name"],
        "brand": product["brand"],
        "size": size,
        "original_price": reference_price,
        "final_price": final_price,
        "discount": discount,
        "discount_type": product.get(
            "binaryPrice", {}
        ).get("discountType", "unknown"),
        "url": product_url,
    }


def build_message(deals):
    lines = [
        "🛍️ Trendyol Deal Tracker",
        "🧪 گزارش آزمایشی داده واقعی",
        ""
    ]

    if not deals:
        return "\n".join(lines + [
            "محصولی با شرایط موردنظر پیدا نشد."
        ])

    for index, deal in enumerate(deals, start=1):
        lines.extend([
            f"{index}. {deal['brand']} - {deal['name']}",
            f"📏 سایز: {deal['size'] or 'بدون سایز'}",
            f"💰 قیمت قبلی: {deal['original_price']} TL",
            f"✅ قیمت نهایی: {deal['final_price']} TL",
            f"🔥 تخفیف تبلیغاتی: {deal['discount']}%",
            f"🏷️ نوع تخفیف: {deal['discount_type']}",
            f"🔗 {deal['url']}",
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
    product = load_product()
    deal = analyze_product(product)

    deals = [deal] if deal else []
    deals.sort(key=lambda item: item["final_price"])

    print(f"Found {len(deals)} matching deals")

    message = build_message(deals)
    send_telegram_message(message)


if __name__ == "__main__":
    main()
