from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

ACCESS_TOKEN = os.environ.get("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_STORE = os.environ.get("SHOPIFY_STORE")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("📥 Incoming customer data:\n", data)

    if not data or "id" not in data:
        print("❌ Invalid payload - missing customer ID.")
        return jsonify({"error": "Missing customer ID"}), 400

    customer_id = data["id"]
    # Strip GraphQL ID if needed
    if isinstance(customer_id, str) and customer_id.startswith("gid://"):
        customer_id = customer_id.split("/")[-1]

    print(f"🔍 Normalized customer ID: {customer_id}")

    metafields = []
    for key, value in data.items():
        if key in ["id", "email"] or value in [None, ""]:
            print(f"⏩ Skipping empty or reserved field: {key}")
            continue

        # Add correct metafield type for specific fields
        metafield_type = "single_line_text_field"
        if key == "company_website":
            metafield_type = "url"
        elif key == "internal_notes":
            metafield_type = "multi_line_text_field"

        metafields.append({
            "namespace": "custom",
            "key": key,
            "value": value,
            "type": metafield_type
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
