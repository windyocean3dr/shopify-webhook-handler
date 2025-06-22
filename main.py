from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE")
API_VERSION = "2024-01"

# List of expected customer metafields
METAFIELDS = [
    "billing_first_name", "billing_last_name", "billing_email", "billing_phone",
    "billing_country", "billing_province", "billing_postal_code", "billing_city",
    "billing_address_1", "billing_address_2", "shipping_first_name", "shipping_last_name",
    "shipping_email", "shipping_phone", "shipping_country", "shipping_province",
    "shipping_postal_code", "shipping_city", "shipping_address_1", "shipping_address_2",
    "preferred_language", "business_type", "business_type_other", "company_name",
    "company_website", "primary_phone", "role", "role_other", "internal_notes",
    "sales_agent", "access_status", "message_notes"
]

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_json()
    print("\n📩 Incoming Payload:", payload)

    customer_id = payload.get("id")
    if not customer_id:
        return jsonify({"error": "Missing customer ID"}), 400

    success = []
    failed = []

    for key in METAFIELDS:
        value = payload.get(key)
        if value is not None:
            success_bool = write_metafield(customer_id, key, value)
            if success_bool:
                success.append(key)
            else:
                failed.append(key)

    print(f"\n✅ Metafields updated: {success}")
    if failed:
        print(f"\n⚠️ Failed to update: {failed}")

    return jsonify({"status": "ok", "updated": success, "failed": failed}), 200

def write_metafield(customer_id, key, value):
    url = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/{API_VERSION}/metafields.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": ACCESS_TOKEN
    }

    metafield_data = {
        "metafield": {
            "namespace": "custom",
            "key": key,
            "value": value,
            "type": "single_line_text_field",
            "owner_id": customer_id,
            "owner_resource": "customer"
        }
    }

    response = requests.post(url, json=metafield_data, headers=headers)
    if response.status_code in [200, 201]:
        return True
    else:
        print(f"❌ Error writing {key}: {response.status_code} - {response.text}")
        return False

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
