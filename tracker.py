
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

MIN_DISCOUNT = 30
ALLOWED_SHOE_SIZES = {"38.5", "39"}

SHOE_CATEGORIES = {
    "Çizme", "Bot", "Ayakkabı", "Sneaker",
    "Spor Ayakkabı", "Topuklu Ayakkabı"
}

BASE_URL = "https://www.trendyol.com"


def load_products():
    file_path = Path(__file__).with_name(
        "trendyol_products.json"
    )

    with file_path.open("r", encoding="utf-8") as file:
        products = json.load(file)

    if not isinstance(products, list):
        raise ValueError("Expected a list of products")

    return products


def calculate_discount(original_price, final_price):
    if original_price <= 0:
        return 0

    return round(
        (original_price - final_price) / original_price * 100,
        1
    )


def analyze_product(product):
    category = product.get("category", {}).get("name", "")

    size = str(product.get("variantValue") or "")

    if category in SHOE_CATEGORIES:
        if size not in ALLOWED_SHOE_SIZES:
            return None

    if product.get("tagStockBar", {}).get("isSoldOut") is True:
        return None

    price = product.get("price", {})

    original_price = price.get("current")
    final_price = price.get("discountedPrice")

    if original_price is None or final_price is None:
        return None

    original_price = float(original_price)
    final_price = float(final_price)

    discount = calculate_discount(
        original_price, final_price
    )

    if discount < MIN_DISCOUNT:
        return None

    relative_url = product.get("url", "")

    if not relative_url:
        return None

    if relative_url.startswith("https://"):
        url = relative_url
    else:
        url = BASE_URL + "/" + relative_url.lstrip("/")

    return {
        "id": product["id"],
        "name": product["name"],
        "brand": product.get("brand", "Unknown"),
        "category": category,
        "size": size,
        "original_price": original_price,
        "final_price": final_price,
        "discount": discount,
        "discount_type": product.get(
            "binaryPrice", {}
        ).get("discountType", "unknown"),
        "url": url,
    }


def find_best_deals(products):
    unique_deals = {}

    for product in products:
        deal = analyze_product(product)

        if deal is None:
            continue

        key = (deal["id"], deal["size"])

        previous = unique_deals.get(key)

        if previous is None or (
            deal["final_price"] < previous["final_price"]
        ):
            unique_deals[key] = deal

    return sorted(
        unique_deals.values(),
        key=lambda item: item["final_price"]
    )


def build_message(deals):
    lines = [
        "🛍️ Trendyol Deal Tracker",
        "🧪 گزارش آزمایشی محصولات",
        f"🔥 حداقل تخفیف: {MIN_DISCOUNT}%",
        f"📦 تعداد محصولات: {len(deals)}",
        ""
    ]

    if not deals:
        lines.append("محصول مناسبی پیدا نشد.")

    for index, deal in enumerate(deals, start=1):
        lines.extend([
            f"{index}. {deal['brand']} - {deal['name']}",
            f"📂 دسته: {deal['category']}",
            f"📏 سایز: {deal['size'] or 'نامشخص'}",
            f"💰 قیمت مرجع: {deal['original_price']:,.2f} TL",
            f"✅ قیمت تخفیفی: {deal['final_price']:,.2f} TL",
            f"🔥 تخفیف اعلامی: {deal['discount']}%",
            f"🏷️ نوع: {deal['discount_type']}",
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
    products = load_products()
    deals = find_best_deals(products)

    print(f"Products loaded: {len(products)}")
    print(f"Matching deals: {len(deals)}")

    message = build_message(deals)
    send_telegram_message(message)


if __name__ == "__main__":
    main()
