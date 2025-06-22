from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file (for local dev)
load_dotenv()

# Flask app
app = Flask(__name__)

# Get API credentials from environment variables
ACCESS_TOKEN = os.environ.get("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_STORE = os.environ.get("SHOPIFY_STORE")

# Webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    # ✅ BONUS: Log full payload for debugging
    print("📥 Incoming full payload:", data)

    if not data or 'id' not in data:
        print("❌ Invalid webhook payload")
        return jsonify({"error": "Invalid webhook data"}), 400

    customer_id = data['id']
    print(f"✅ New customer webhook received: ID {customer_id}")

    # Fetch customer metafields
    metafields = fetch_customer_metafields(customer_id)

    if metafields is not None:
        print(f"📦 Metafields for Customer {customer_id}:")
        for mf in metafields:
            print(f"- {mf['namespace']}.{mf['key']}: {mf['value']}")
    else:
        print("⚠️ Failed to retrieve metafields.")

    return jsonify({"status": "ok"}), 200


def fetch_customer_metafields(customer_id):
    url = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/2024-01/customers/{customer_id}/metafields.json"
    headers = {
        "X-Shopify-Access-Token": ACCESS_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("metafields", [])
    else:
        print(f"❌ Error fetching metafields: {response.status_code}")
        print(response.text)
        return None


# Start Flask app (Render will auto-detect port)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Render sets this automatically
    app.run(host='0.0.0.0', port=port)
