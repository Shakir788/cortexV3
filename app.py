from flask import Flask, request, jsonify
import requests
import os
import json 
from dotenv import load_dotenv
import urllib3 

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load all credentials from the .env file
load_dotenv() 

# Import the existing chat handler logic and new image/audio function
from chat_handler import chat_with_ai, handle_special_commands, analyze_image, transcribe_audio 

app = Flask(__name__)

# --- Global Settings ---
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "MOHAMMAD_CORTEX_2025")

CHAT_CONTEXT_HISTORY = {} 

def send_whatsapp_interactive_message(to_number, message_payload):
    """
    Sends a message back to the user via WhatsApp API.
    message_payload can be a simple string (text) or a dictionary (interactive).
    """
    
    WA_TOKEN = os.getenv("WA_ACCESS_TOKEN")
    WA_PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
    API_VERSION = "v18.0"
    API_URL = f"https://graph.facebook.com/{API_VERSION}/{WA_PHONE_NUMBER_ID}/messages" 

    if not WA_TOKEN or not WA_PHONE_NUMBER_ID:
        print("ERROR: WA Credentials missing (Token or Phone ID)!")
        return {"status": "error", "message": "WA Credentials missing"}

    headers = {"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"}
    
    if isinstance(message_payload, str):
        # Case 1: Simple Text Message
        data = {"messaging_product": "whatsapp", "to": to_number, "type": "text", "text": {"body": message_payload}}
    elif isinstance(message_payload, dict):
        # Case 2: Interactive Message (e.g., Reply Buttons, List Messages)
        data = {"messaging_product": "whatsapp", "to": to_number, "type": "interactive", "interactive": message_payload}
    else:
        print(f"ERROR: Invalid message payload type: {type(message_payload)}")
        return {"status": "error", "message": "Invalid payload type"}
        
    try:
        response = requests.post(API_URL, headers=headers, json=data, verify=False) 
        
        if response.status_code != 200:
            print(f"FATAL API ERROR (Reply Failed): Status={response.status_code} | Response Body={response.text}")
            return {"status": "api_error", "response": response.json()}
        
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"CRITICAL NETWORK ERROR: Could not connect to Meta API. Error: {e}")
        return {"status": "network_fail"}

# --- 1. Webhook Verification (UNMODIFIED) ---
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN: 
        print("Webhook Verified Successfully!")
        return request.args.get("hub.challenge"), 200
    
    print("Verification Failed: Token Mismatch!")
    return "Verification token mismatch", 403

# --- 2. Message Reception (VOICE HANDLER REMOVED FOR STABILITY) ---
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
    except (IndexError, AttributeError):
        return jsonify({"status": "malformed_json_structure"}), 200
    
    from_number = None 
    
    if value.get("statuses"):
        return jsonify({"status": "status_update_ignored"}), 200
    
    if value.get("messages"):
        try:
            message_data = value["messages"][0]
            from_number = message_data.get("from")
            
            if not from_number: return jsonify({"status": "missing_from_number"}), 200
            
            message_text = None
            
            # --- INITIALIZE HISTORY ---
            if from_number not in CHAT_CONTEXT_HISTORY: CHAT_CONTEXT_HISTORY[from_number] = []
            user_history = CHAT_CONTEXT_HISTORY[from_number]

            # --- INTERACTIVE (BUTTON/LIST) MESSAGE HANDLING ---
            if message_data.get("type") == "interactive":
                interactive_data = message_data.get("interactive", {})
                
                if interactive_data.get("type") == "button_reply":
                    message_id = interactive_data["button_reply"]["id"]
                    message_title = interactive_data["button_reply"]["title"]
                    message_text = f"!INTERACTIVE: {message_id} ({message_title})" 
                    
                elif interactive_data.get("type") == "list_reply":
                    message_id = interactive_data["list_reply"]["id"]
                    message_title = interactive_data["list_reply"]["title"]
                    message_text = f"!INTERACTIVE: {message_id} ({message_title})"
                
                send_whatsapp_interactive_message(from_number, f"Cortex: Aapne **{message_title}** chuna hai. Main ab jawab de raha hoon.")

            # --- IMAGE MESSAGE HANDLING (UNMODIFIED) ---
            elif message_data.get("type") == "image":
                media_id = message_data["image"]["id"]
                user_caption = message_data["image"].get("caption", "Analyze this image.")
                
                send_whatsapp_interactive_message(from_number, "Cortex: Photo mil gayi! Thoda samay deejye, main ise samajh raha hoon. 📸")
                
                ai_response = analyze_image(media_id, user_caption)
                
                send_whatsapp_interactive_message(from_number, ai_response)
                
                user_history.append({"role": "user", "content": f"IMAGE: {user_caption}"})
                user_history.append({"role": "assistant", "content": ai_response})
                CHAT_CONTEXT_HISTORY[from_number] = user_history[-10:] 
                
                return jsonify({"status": "image_processed"}), 200
            
            # --- AUDIO MESSAGE HANDLING (NOW UNSUPPORTED) ---
            elif message_data.get("type") == "audio":
                 if from_number:
                     send_whatsapp_interactive_message(from_number, "Cortex: Maafi chahunga, Voice Note feature abhi **Maintenance** mein hai. Kripya **text message** ya **Image** bhejein. 🙏")
                 return jsonify({"status": "unsupported_audio_due_to_timeout"}), 200
                
            # --- TEXT MESSAGE HANDLING (Simple) ---
            elif message_data.get("type") == "text":
                message_text = message_data.get("text", {}).get("body")
            
            # --- OTHER MESSAGE TYPES ---
            else:
                 if from_number:
                     send_whatsapp_interactive_message(from_number, "Cortex: Abhi main sirf text, images, aur buttons samajh sakta hoon, Mohammad!")
                 return jsonify({"status": "unsupported_type"}), 200


            # --- PROCESS TEXT/TRANSCRIPT/INTERACTIVE ID ---
            if message_text:
                
                special_response = handle_special_commands(message_text)
                
                if special_response:
                    send_whatsapp_interactive_message(from_number, special_response)
                
                else:
                    ai_response = chat_with_ai(message_text, user_history)
                    send_whatsapp_interactive_message(from_number, ai_response)
                    
                    user_history.append({"role": "user", "content": message_text})
                    user_history.append({"role": "assistant", "content": ai_response})
                    CHAT_CONTEXT_HISTORY[from_number] = user_history[-10:] 
                    
                return jsonify({"status": "message_processed"}), 200
            
            return jsonify({"status": "message_text_empty"}), 200

        except Exception as e:
            print(f"CRITICAL RUNTIME ERROR: {e}")
            if 'from_number' in locals() and from_number:
                send_whatsapp_interactive_message(from_number, "Cortex: Maafi chahunga, mere system mein kuch gadbad ho gayi. Detail: Check terminal for network errors.")
            
            return jsonify({"status": "runtime_error", "details": str(e)}), 200
    
    return jsonify({"status": "acknowledged"}), 200

if __name__ == "__main__":
    if not os.getenv("WA_ACCESS_TOKEN"):
        print("\nFATAL ERROR: WA_ACCESS_TOKEN is missing in .env file. Please check and restart.")
    else:
        app.run(debug=True, port=5000, use_reloader=False)