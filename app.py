from flask import Flask, request, jsonify
import requests
import os
import json 
from dotenv import load_dotenv
import urllib3 # For SSL bypass

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load all credentials from the .env file (Only needs to be done once)
load_dotenv() 

# Import the existing chat handler logic
from chat_handler import chat_with_ai, handle_special_commands 

app = Flask(__name__)

# --- Global Settings ---
VERIFY_TOKEN = "MOHAMMAD_CORTEX_2025"  
# NOTE: WA_TOKEN aur WA_PHONE_NUMBER_ID ko GLOBAL SE HATA DIYA HAI 
# TAAKI WOH FUNCTION MEIN SAHI LOAD HO SAKEN.

CHAT_CONTEXT_HISTORY = {} 

def send_whatsapp_message(to_number, text_message):
    """Sends a message back to the user via WhatsApp API."""
    
    # --- CRITICAL FIX: Variables ko function ke andar load karo ---
    WA_TOKEN = os.getenv("WA_ACCESS_TOKEN")
    WA_PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
    API_VERSION = "v18.0"
    API_URL = f"https://graph.facebook.com/{API_VERSION}/{WA_PHONE_NUMBER_ID}/messages" 
    # -------------------------------------------------------------

    if not WA_TOKEN or not WA_PHONE_NUMBER_ID:
        # Ab yeh ERROR nahi aana chahiye agar .env theek hai
        print("ERROR: WA Credentials missing (Token or Phone ID) at send time!")
        return {"status": "error", "message": "WA Credentials missing"}

    headers = {
        "Authorization": f"Bearer {WA_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text_message},
    }
    
    try:
        # --- FINAL FIX: SSL VERIFICATION BYPASS (CRITICAL FIX) ---
        response = requests.post(API_URL, headers=headers, json=data, verify=False) 
        
        if response.status_code != 200:
            print(f"FATAL API ERROR (Reply Failed): Status={response.status_code} | Response Body={response.text}")
            return {"status": "api_error", "response": response.json()}
        
        print("SUCCESS: Message sent to Meta API.")
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"CRITICAL NETWORK ERROR: Could not connect to Meta API. Error: {e}")
        return {"status": "network_fail"}

# --- Webhook and Message Handler (Rest of the code is unchanged) ---
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    # Token check is still outside (simpler check for verification only)
    VERIFY_TOKEN = "MOHAMMAD_CORTEX_2025" 
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        print("Webhook Verified Successfully!")
        return request.args.get("hub.challenge"), 200
    
    print("Verification Failed: Token Mismatch!")
    return "Verification token mismatch", 403

@app.route("/webhook", methods=["POST"])
def webhook_handler():
    data = request.get_json()
    
    if data:
        print("--- Received Webhook Data ---")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("-----------------------------")

    try:
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        
        from_number = None 
        if value.get("statuses"):
            print("Status update received (read/sent), ignoring.")
            return jsonify({"status": "status_update_ignored"}), 200
        
        if value.get("messages"):
            message_data = value["messages"][0]
            from_number = message_data.get("from")
            
            if not from_number:
                return jsonify({"status": "missing_from_number"}), 200
            
            if message_data.get("type") == "text":
                message_text = message_data.get("text", {}).get("body")
                
                if not message_text:
                     return jsonify({"status": "empty_message_body"}), 200
                
                if from_number not in CHAT_CONTEXT_HISTORY:
                    CHAT_CONTEXT_HISTORY[from_number] = []

                user_history = CHAT_CONTEXT_HISTORY[from_number]
                special_response = handle_special_commands(message_text)
                
                if special_response:
                    send_whatsapp_message(from_number, special_response)
                else:
                    ai_response = chat_with_ai(message_text, user_history)
                    send_whatsapp_message(from_number, ai_response)
                    
                    user_history.append({"role": "user", "content": message_text})
                    user_history.append({"role": "assistant", "content": ai_response})
                    CHAT_CONTEXT_HISTORY[from_number] = user_history[-10:] 
                    
                return jsonify({"status": "message_processed"}), 200

            else:
                if from_number:
                    send_whatsapp_message(from_number, "Cortex: Abhi main sirf text messages samajh sakta hoon, Mohammad!")
                return jsonify({"status": "unsupported_type"}), 200

    except Exception as e:
        print(f"CRITICAL RUNTIME ERROR: {e}")
        if 'from_number' in locals() and from_number:
                 send_whatsapp_message(from_number, "Cortex: Maafi chahunga, mere system mein kuch gadbad ho gayi. Detail: Check terminal for network errors.")
            
        return jsonify({"status": "runtime_error", "details": str(e)}), 200
    
    return jsonify({"status": "acknowledged"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000, use_reloader=False)