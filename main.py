from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv

# Load .env
load_dotenv()

app = Flask(__name__)

ACCESS_TOKEN = os.environ.get("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_STORE = os.environ.get("SHOPIFY_STORE")

# All your metafield keys
METAFIELD_KEYS = [
    "billing_last_name", "billing_first_name", "shipping_email", "shipping_phone",
    "shipping_country", "shipping_province", "shipping_postal_code", "shipping_city",
    "shipping_address_2", "shipping_address_1", "shipping_last_name", "shipping_first_name",
    "preferred_language", "business_type_other", "business_type", "company_website",
    "company_name", "primary_phone", "role_other", "role", "internal_notes",
    "sales_agent", "access_status", "message_notes", "billing_email", "billing_phone",
    "billing_country", "billing_province", "billing_postal_code", "billing_city",
    "billing_address_2", "billing_address_1"
]

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("📥 Full payload received:", data)

    # Extract numeric ID from Shopify GID format
    gid = data.get("id", "")
    if "Customer/" not in gid:
        return jsonify({"error": "Invalid customer GID"}), 400

    customer_id = gid.split("/")[-1]
    print(f"✅ Processing customer ID: {customer_id}")

    # Build metafields to update
    metafields_payload = []

    for key in METAFIELD_KEYS:
        full_key = f"custom.{key}"
        value = data.get(full_key)
        if value:  # Only include if value is not None or empty
            metafields_payload.append({
                "namespace": "custom",
                "key": key,
                "type": "single_line_text_field",
                "value": str(value)
            })

    if metafields_payload:
        success = write_metafields(customer_id, metafields_payload)
        if success:
            print(f"📝 Updated {len(metafields_payload)} metafields for customer {customer_id}")
        else:
            print("❌ Failed to update metafields")
    else:
        print("⚠️ No metafield data to update")

    return jsonify({"status": "ok"}), 200

def write_metafields(customer_id, metafields):
    url = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/2024-01/customers/{customer_id}/metafields.json"
    headers = {
        "X-Shopify-Access-Token": ACCESS_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = { "metafields": metafields }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code in [200, 201]:
        return True
    else:
        print("❌ Shopify API error:", response.status_code)
        print(response.text)
        return False

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
