
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

MIN_DISCOUNT = 30
ALLOWED_SHOE_SIZES = {"38.5", "39"}
SHOE_CATEGORIES = {
    "çizme", "bot", "ayakkabı", "sneaker",
    "spor ayakkabı", "topuklu ayakkabı"
}
BASE_URL = "https://www.trendyol.com"

ROOT = Path(__file__).parent
PRODUCTS_FILE = ROOT / "trendyol_products.json"
HISTORY_FILE = ROOT / "price_history.json"


def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_history(history):
    with HISTORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=2)
        file.write("\n")


def calculate_discount(reference_price, final_price):
    if reference_price <= 0:
        return 0

    return round(
        (reference_price - final_price) / reference_price * 100,
        1
    )


def analyze_product(product):
    category = product.get("category", {}).get("name", "")
    size = str(product.get("variantValue") or "")

    if category.casefold() in SHOE_CATEGORIES:
        if size not in ALLOWED_SHOE_SIZES:
            return None

    stock = product.get("tagStockBar", {})
    if stock.get("isSoldOut") is True:
        return None

    price = product.get("price", {})
    reference_price = price.get("current")
    final_price = price.get("discountedPrice")

    if reference_price is None or final_price is None:
        return None

    reference_price = float(reference_price)
    final_price = float(final_price)

    if reference_price <= 0 or final_price <= 0:
        return None

    discount = calculate_discount(reference_price, final_price)

    relative_url = product.get("url", "")
    if not relative_url:
        return None

    if relative_url.startswith("https://"):
        product_url = relative_url
    else:
        product_url = BASE_URL + "/" + relative_url.lstrip("/")

    merchant_id = product.get("merchantId", "unknown")
    product_key = f"{product['id']}:{size}:{merchant_id}"

    return {
        "key": product_key,
        "name": product["name"],
        "brand": product.get("brand", "Unknown"),
        "category": category,
        "size": size,
        "reference_price": reference_price,
        "final_price": final_price,
        "discount": discount,
        "discount_type": product.get(
            "binaryPrice", {}
        ).get("discountType", "unknown"),
        "url": product_url,
    }


def find_price_changes(products, history):
    latest_products = {}

    for product in products:
        deal = analyze_product(product)

        if deal is None:
            continue

        key = deal["key"]
        previous = latest_products.get(key)

        if previous is None or deal["final_price"] < previous["final_price"]:
            latest_products[key] = deal

    price_drops = []

    for key, deal in latest_products.items():
        current_price = deal["final_price"]
        old_record = history.get(key)

        if old_record is not None:
            old_price = float(old_record["price"])

            if current_price < old_price and deal["discount"] >= MIN_DISCOUNT:
                price_drop = round(old_price - current_price, 2)
                price_drop_percent = round(
                    price_drop / old_price * 100, 1
                )

                price_drops.append({
                    **deal,
                    "previous_price": old_price,
                    "price_drop": price_drop,
                    "price_drop_percent": price_drop_percent,
                })

        history[key] = {
            "price": current_price,
            "name": deal["name"],
            "brand": deal["brand"],
        }

    price_drops.sort(key=lambda item: item["final_price"])
    return price_drops


def build_messages(price_drops):
    header = (
        "🔥 کاهش قیمت در Trendyol!\n"
        f"📦 تعداد پیشنهادهای جدید: {len(price_drops)}\n"
        f"🏷️ حداقل تخفیف تبلیغاتی: {MIN_DISCOUNT}%\n\n"
    )

    messages = []
    message = header

    for index, deal in enumerate(price_drops, start=1):
        entry = (
            f"{index}. {deal['brand']} - {deal['name']}\n"
            f"📏 سایز: {deal['size'] or 'نامشخص'}\n"
            f"💰 قیمت قبلی: {deal['previous_price']:,.2f} TL\n"
            f"✅ قیمت جدید: {deal['final_price']:,.2f} TL\n"
            f"📉 کاهش قیمت: {deal['price_drop']:,.2f} TL "
            f"({deal['price_drop_percent']}%)\n"
            f"🔥 تخفیف تبلیغاتی: {deal['discount']}%\n"
            f"🏷️ نوع تخفیف: {deal['discount_type']}\n"
            f"🔗 {deal['url']}\n\n"
        )

        # Keep Telegram messages below its text length limit.
        if len(message) + len(entry) > 3500:
            messages.append(message)
            message = header

        message += entry

    if message.strip() != header.strip():
        messages.append(message)

    return messages


def send_telegram_message(message):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
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


def main():
    products = load_json(PRODUCTS_FILE)
    history = load_json(HISTORY_FILE)

    if not isinstance(products, list):
        raise ValueError("Products must be a list")

    if not isinstance(history, dict):
        raise ValueError("Price history must be an object")

    price_drops = find_price_changes(products, history)

    print(f"Products loaded: {len(products)}")
    print(f"Price drops found: {len(price_drops)}")

    if price_drops:
        messages = build_messages(price_drops)

        for message in messages:
            send_telegram_message(message)

        print("Telegram alerts sent successfully!")
    else:
        print("No new price drops. No Telegram alert sent.")

    save_history(history)
    print("Price history saved.")


if __name__ == "__main__":
    main()
