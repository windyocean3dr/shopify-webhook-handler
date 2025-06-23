from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv
import inflection

load_dotenv()
app = Flask(__name__)

ACCESS_TOKEN = os.environ.get("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_STORE = os.environ.get("SHOPIFY_STORE")

# ✅ Define known valid metafields and their expected types
VALID_METAFIELDS = {
    "billing_first_name": "single_line_text_field",
    "billing_last_name": "single_line_text_field",
    "billing_email": "single_line_text_field",
    "billing_phone": "single_line_text_field",
    "billing_country": "single_line_text_field",
    "billing_province": "single_line_text_field",
    "billing_postal_code": "single_line_text_field",
    "billing_city": "single_line_text_field",
    "billing_address_1": "single_line_text_field",
    "billing_address_2": "single_line_text_field",
    "shipping_first_name": "single_line_text_field",
    "shipping_last_name": "single_line_text_field",
    "shipping_email": "single_line_text_field",
    "shipping_phone": "single_line_text_field",
    "shipping_country": "single_line_text_field",
    "shipping_province": "single_line_text_field",
    "shipping_postal_code": "single_line_text_field",
    "shipping_city": "single_line_text_field",
    "shipping_address_1": "single_line_text_field",
    "shipping_address_2": "single_line_text_field",
    "preferred_language": "single_line_text_field",
    "business_type": "single_line_text_field",
    "business_type_other": "single_line_text_field",
    "company_name": "single_line_text_field",
    "company_website": "url",
    "primary_phone": "single_line_text_field",
    "role": "single_line_text_field",
    "role_other": "single_line_text_field",
    "internal_notes": "multi_line_text_field",
    "sales_agent": "single_line_text_field",
    "access_status": "single_line_text_field",
    "message_notes": "single_line_text_field"
}

def parse_note_to_dict(note):
    lines = note.strip().split("\n")
    parsed = {}
    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            parsed[key.strip()] = value.strip()
    return parsed

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("📥 Incoming customer data:\n", data)

    if not data or "id" not in data:
        print("❌ Invalid payload - missing customer ID.")
        return jsonify({"error": "Missing customer ID"}), 400

    customer_id = data["id"]
    if isinstance(customer_id, str) and customer_id.startswith("gid://"):
        customer_id = customer_id.split("/")[-1]

    print(f"🔍 Normalized customer ID: {customer_id}")

    merged_data = dict(data)  # Copy original data

    if "note" in data and data["note"]:
        parsed_note = parse_note_to_dict(data["note"])
        merged_data.update(parsed_note)

    metafields = []
    for key, value in merged_data.items():
        if key in ["id", "email"] or value is None or str(value).strip() == "":
            print(f"⏩ Skipping empty or reserved field: {key}")
            continue

        normalized_key = inflection.underscore(key)

        if normalized_key not in VALID_METAFIELDS:
            print(f"⚠️ Skipping unknown or unsupported field: {key}")
            continue

        metafields.append({
            "namespace": "custom",
            "key": normalized_key,
            "value": str(value),
            "type": VALID_METAFIELDS[normalized_key]
        })

    if not metafields:
        print("⚠️ No valid metafields to update.")
        return jsonify({"status": "skipped"}), 200

    for metafield in metafields:
        success = update_metafield(customer_id, metafield)
        if success:
            print(f"✅ Updated {metafield['namespace']}.{metafield['key']}")
        else:
            print(f"❌ Failed to update {metafield['namespace']}.{metafield['key']}")

    return jsonify({"status": "ok"}), 200

def update_metafield(customer_id, metafield):
    url = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/2024-01/customers/{customer_id}/metafields.json"
    headers = {
        "X-Shopify-Access-Token": ACCESS_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "metafield": metafield
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        return True
    else:
        print(f"❌ Error updating metafield {metafield['key']}: {response.status_code}")
        print(response.text)
        return False

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
