from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

ACCESS_TOKEN = os.environ.get("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_STORE = os.environ.get("SHOPIFY_STORE")

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        raw_data = request.data.decode('utf-8')
        print("📨 Raw request body:", raw_data)

        data = request.get_json(force=True)
        if not data or 'id' not in data:
            print("⚠️ Webhook missing 'id' field.")
            return jsonify({"error": "Invalid webhook data"}), 400

        customer_id = data['id']
        print(f"✅ Webhook received for customer ID: {customer_id}")

        metafields = fetch_customer_metafields(customer_id)

        if metafields is not None:
            print(f"📦 Metafields for customer {customer_id}:")
            for mf in metafields:
                print(f"- {mf['namespace']}.{mf['key']}: {mf['value']}")
        else:
            print("❌ Failed to fetch metafields.")

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print(f"❌ Exception in /webhook: {str(e)}")
        return jsonify({"error": str(e)}), 400

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
        print(f"❌ HTTP {response.status_code} while fetching metafields")
        print(response.text)
        return None

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
