from flask import Flask, request, jsonify
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Environment config
ACCESS_TOKEN = os.environ.get("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_STORE = os.environ.get("SHOPIFY_STORE")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    # Log full payload for debugging
    print("\n📥 Incoming customer data:")
    print(json.dumps(data, indent=2))

    # Get Shopify customer ID from GraphQL ID
    customer_id = data.get("id", "")
    if customer_id.startswith("gid://"):
        customer_id = customer_id.split("/")[-1]

    if not customer_id:
        print("❌ Missing or invalid customer ID")
        return jsonify({"error": "Invalid customer ID"}), 400

    # Loop through all fields and update metafields
    for key, value in data.items():
        if key in ["id", "email"]:
            continue
        namespace = "custom"
        update_metafield(customer_id, namespace, key, value)

    return jsonify({"status": "ok"}), 200

def update_metafield(customer_id, namespace, key, value):
    url = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/2024-01/customers/{customer_id}/metafields.json"
    headers = {
        "X-Shopify-Access-Token": ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "metafield": {
            "namespace": namespace,
            "key": key,
            "value": value,
            "type": "single_line_text_field"
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        print(f"✅ Metafield {namespace}.{key} set to '{value}'")
    else:
        print(f"❌ Error updating metafield {namespace}.{key}: {response.status_code}")
        print(response.text)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
