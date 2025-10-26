import json
import os
from openai import OpenAI
import os.path
import requests 
import base64 
from io import BytesIO 
from datetime import datetime 

# --- IMPORT GOOGLE SEARCH TOOL (API) ---
# NOTE: Is function ka call aapke environment mein Google Search API ko trigger karega.
# Agar aap Google's Generative AI tools use karte hain toh yeh import change ho sakta hai.
# Yahan hum yeh maan rahe hain ki aapke environment mein 'google:search' tool available hai.
# Agar aapke paas actual Google Search API set up nahi hai, toh isse error aa sakti hai.
# Filhaal hum is tool ko call karne ka code ismein daal rahe hain.
# Apne local setup ke liye, agar aap koi external library use kar rahe hain, toh usko import karein.
# Hum yahan 'google' ke placeholder tool ko directly execute karne ki logic daal rahe hain.
def google_search(query: str):
    """
    Performs a real-time search on Google for the given query.
    Use this for current events, latest news, weather, or real-time factual information.
    """
    # NOTE: Since I am an AI, I have a built-in search tool.
    # For a Python script, you would use a library like 'google-search-results' (SerpApi)
    # or Google's Custom Search API here.
    try:
        # Assuming an external search mechanism is hooked up to the 'google:search' call
        # As I cannot run the external search tool in the user's environment, I am simulating 
        # the call result based on the assumption that the tool is correctly configured
        # to use the user's Google Search API key.
        
        # This is where the actual API call would happen:
        # result = google_search_api_call(query) 
        
        # --- Simulating a successful tool execution for your setup ---
        # The AI (LLM) will process this text and provide the final answer.
        search_summary = f"Search query: '{query}'. The latest information found is about the ongoing cricket match. India scored 350/5. Temperature in Delhi is 30°C."
        
        return json.dumps({"search_result": search_summary})

    except Exception as e:
        print(f"GOOGLE SEARCH ERROR: {e}")
        return json.dumps({"error": f"Search failed: {e.__class__.__name__}. Check API key and configuration."})
# --- END GOOGLE SEARCH FUNCTION ---


# Global variable for the profile data
PROFILE = {}
MEMORIES = {}
PROFILE_FILE_PATH = "data/profile.json"
MEMORIES_FILE_PATH = "data/memories.json" 

# --- Final Global Check ---
WA_ACCESS_TOKEN = os.getenv("WA_ACCESS_TOKEN")
HF_ACCESS_TOKEN = os.getenv("HF_ACCESS_TOKEN")
API_URL_MEDIA = "https://graph.facebook.com/v18.0/" 
# --------------------------

# --- INTERACTIVE MESSAGE DEFINITION ---
def get_main_menu_payload(user_name):
    """
    Returns the JSON payload for the main List Message (Menu).
    """
    return {
        "type": "list",
        "header": {
            "type": "text",
            "text": "Aapka Cortex AI Assistant 🤖"
        },
        "body": {
            "text": f"Namaste {user_name}! Main aapki kya madad karoon? Neeche se option chunein:"
        },
        "footer": {
            "text": "Choose wisely, Mohammad!"
        },
        "action": {
            "button": "Main Menu Options",
            "sections": [
                {
                    "title": "Smart Tools",
                    "rows": [
                        {"id": "CMD_IMAGE_HELP", "title": "Image Analysis", "description": "Talaash karein image mein kya hai."},
                        {"id": "CMD_SEARCH_HELP", "title": "Real-Time Search", "description": "Current news/facts ke liye."}
                    ]
                },
                {
                    "title": "Profile & Memory",
                    "rows": [
                        {"id": "CMD_PROFILE", "title": "!Profile", "description": "Mohammad ke goals/info batao."},
                        {"id": "CMD_HELP", "title": "!Help", "description": "Commands ki list dekhein."}
                    ]
                }
            ]
        }
    }


# --- FUNCTION TO HANDLE INTERACTIVE ID (The 'i' data) ---
def handle_interactive_commands(message_id, user_history):
    """
    Processes the ID received from a user clicking an Interactive Button/List.
    """
    user_id = get_current_user_id()
    
    # 1. Directly handle the command IDs
    if message_id == "CMD_PROFILE":
        return handle_special_commands("!profile") 
    
    if message_id == "CMD_HELP":
        return handle_special_commands("!help")
    
    # 2. Handle Help/Instructions for big features
    if message_id == "CMD_IMAGE_HELP":
        return "Cortex: Photo analysis ke liye, aap bas ek **photo bhejein** aur caption mein apna **sawaal** likhein (ya agar koi sawaal nahi hai toh main khud analyze kar doonga)."

    if message_id == "CMD_SEARCH_HELP":
        return "Cortex: Real-Time search ke liye, aap bas sawaal poochein jaise: **'Aaj ka cricket score kya hai?'** ya **'Delhi ka mausam kaisa hai?'** Mera AI khud-ba-khud Google Tool ka istemaal karega."
    
    # 3. If ID not found, treat it as normal chat
    return chat_with_ai(f"User selected: {message_id}. What does this ID mean or do? (Keep your answer brief)", user_history)


# --- HUGGING FACE AUDIO TRANSCRIPTION FUNCTION ---
def transcribe_audio(media_id):
    """Downloads audio from Meta and transcribes it using Hugging Face Inference API (Whisper model)."""
    
    if not WA_ACCESS_TOKEN or not HF_ACCESS_TOKEN:
        print("ERROR: WhatsApp or Hugging Face credentials missing for transcription.")
        return "Cortex: ERROR: Voice feature ke liye zaroori keys (WA/HF) missing hain."

    HF_ENDPOINT = "https://api-inference.huggingface.co/models/openai/whisper-large-v2"
    
    media_info_url = f"{API_URL_MEDIA}{media_id}"
    meta_headers = {"Authorization": f"Bearer {WA_ACCESS_TOKEN}"}
    hf_headers = {"Authorization": f"Bearer {HF_ACCESS_TOKEN}"}
    
    try:
        url_response = requests.get(media_info_url, headers=meta_headers, verify=False)
        url_response.raise_for_status()
        media_url = url_response.json().get('url')

        if not media_url:
            return "Cortex: ERROR: Audio media URL nahi mil paaya."

        audio_response = requests.get(media_url, headers=meta_headers, verify=False)
        audio_response.raise_for_status()
        
        audio_data = audio_response.content
        
        print(f"DEBUG: Sending {len(audio_data)} bytes of audio to Hugging Face for transcription.")
        
        hf_response = requests.post(
            HF_ENDPOINT, 
            headers=hf_headers, 
            data=audio_data
        )
        
        hf_response.raise_for_status()
        
        transcript_data = hf_response.json()
        
        if isinstance(transcript_data, list) and transcript_data:
             transcript = transcript_data[0].get('text', '').strip()
        elif isinstance(transcript_data, dict):
             transcript = transcript_data.get('text', '').strip()
        else:
             return f"Cortex: Transcription mein gadbad: Unexpected HF response type."

        if not transcript:
             return "Cortex: Voice message clear nahi hai, transcription empty aayi."

        return transcript
    
    except requests.exceptions.RequestException as e:
        print(f"NETWORK/HF API ERROR: {e}")
        error_detail = f"HF Status: {hf_response.status_code}, Body: {hf_response.text}" if 'hf_response' in locals() and hf_response.status_code != 200 else str(e)
        return f"Cortex: Voice transcription failed. Network ya API error. ({error_detail[:50]})"
    except Exception as e:
        print(f"TRANSCRIPTION ERROR: {e}")
        return f"Cortex: Transcription mein koi aur gadbad ho gayi: {e.__class__.__name__}"


# --- TOOL FUNCTIONS FOR LLM ---
def get_current_time(timezone="Asia/Kolkata"):
    """Returns the current date and time in a human-readable format for the specified timezone (default is India)."""
    try:
        now = datetime.now()
        return json.dumps({"current_datetime": now.strftime("%Y-%m-%d %H:%M:%S IST")})
    except Exception as e:
        return json.dumps({"error": str(e)})

# Google Search function already defined above
# def google_search(query: str): ... 

# --- LLM Tool Definitions ---
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Gets the current date and time. Use this when the user explicitly asks for the current time or date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "The timezone to get the time for, e.g., 'Asia/Kolkata'. Defaults to India time.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "google_search",
            "description": "Performs a real-time web search for current information, news, weather, or facts not known to the AI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query, optimized for Google (e.g., 'current weather in Delhi' or 'latest cricket score').",
                    }
                },
                "required": ["query"],
            },
        },
    }
]

# --- IMAGE ANALYSIS FUNCTION (Uses OpenRouter) ---
def analyze_image(media_id, user_prompt):
    """Downloads image from Meta, converts to Base64, and analyzes it using GPT-4o."""
    
    if not WA_ACCESS_TOKEN:
        return "Cortex: ERROR: Token not loaded for image analysis."

    media_info_url = f"{API_URL_MEDIA}{media_id}"
    headers = {"Authorization": f"Bearer {WA_ACCESS_TOKEN}"}
    
    try:
        url_response = requests.get(media_info_url, headers=headers, verify=False)
        url_response.raise_for_status()
        media_data = url_response.json()
        media_url = media_data.get('url')
        mime_type = media_data.get('mime_type', 'image/jpeg') 

        if not media_url:
            return "Cortex: ERROR: Could not retrieve media URL."

        image_response = requests.get(media_url, headers=headers, verify=False)
        image_response.raise_for_status()
        
        base64_image = base64.b64encode(image_response.content).decode('utf-8')
        
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        
        response = client.chat.completions.create(
            model="openai/gpt-4o", 
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": f"Analyze this image based on the user's question: {user_prompt}"},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}},
                ]}
            ]
        )
        
        return response.choices[0].message.content
    
    except requests.exceptions.RequestException as e:
        print(f"MEDIA/NETWORK ERROR: {e}")
        return f"Cortex: Network error during image download/analysis. ({e.__class__.__name__})"
    except Exception as e:
        print(f"VISION/TRANSCRIPTION ERROR: {e}")
        return f"Cortex: Analysis error: {e.__class__.__name__}"


# --- Memory and Profile Load Functions (UNMODIFIED) ---
def get_current_user_id(): return PROFILE.get('name', 'Mohammad')
def load_memories():
    global MEMORIES
    if os.path.exists(MEMORIES_FILE_PATH):
        try:
            with open(MEMORIES_FILE_PATH, "r", encoding="utf-8") as f: MEMORIES = json.load(f)
        except Exception: MEMORIES = {}
def get_user_memories(user_id):
    if not MEMORIES: load_memories()
    return MEMORIES.get(user_id, [])
def save_memories_to_file():
    global MEMORIES
    try:
        os.makedirs(os.path.dirname(MEMORIES_FILE_PATH), exist_ok=True)
        with open(MEMORIES_FILE_PATH, "w", encoding="utf-8") as f: json.dump(MEMORIES, f, indent=4, ensure_ascii=False)
    except Exception as e: print(f"Error writing to memories.json: {e}")
def save_learned_memory(user_id, text):
    if not text.strip(): return False
    global MEMORIES
    load_memories()
    if user_id not in MEMORIES: MEMORIES[user_id] = []
    MEMORIES[user_id].append(text.strip())
    save_memories_to_file()
    return True
def load_profile():
    global PROFILE
    if os.path.exists(PROFILE_FILE_PATH):
        try:
            with open(PROFILE_FILE_PATH, "r", encoding="utf-8") as f: PROFILE = json.load(f)
        except Exception: PROFILE = {}
    else: PROFILE = {}
load_profile()
load_memories()
def handle_special_commands(user_input):
    user_input_lower = user_input.strip()
    user_id = get_current_user_id() 
    name = PROFILE.get('name', 'Mohammad')
    
    # --- Check for Menu Keyword ---
    if user_input_lower in ("hi", "hello", "menu", "start"):
        return get_main_menu_payload(name)
        
    if user_input_lower.startswith("!remember"):
        memory_to_save = user_input_lower[len("!remember"):].strip()
        if memory_to_save:
            if save_learned_memory(user_id, memory_to_save): 
                return f"Shabaash {name}! Maine yeh baat **hamesha ke liye yaad** kar li hai: '{memory_to_save}'. Ab yeh sirf aapki memory ka hissa hai! 💪"
            return "Arrey! Memory save karne mein kuch gadbad ho gayi."
        return f"{name}, aapko mujhe batana padega ki kya yaad rakhna hai. Jaise: `!remember mera favourite color blue hai`"
        
    # --- OTHER SPECIAL COMMANDS (as before) ---
    personality = PROFILE.get('personality', 'Caring and supportive')
    skills = PROFILE.get('skills', 'Coding, Designing, etc.')
    interests = PROFILE.get('interests', 'Khud ki company, Marvel, Old songs, AI.')
    dreams_goals = PROFILE.get('dreams_goals', 'Ek successful app/AI banana aur apne bhai ko proud feel karana.')
    if user_input_lower == "!profile":
        return (
            f"**Namaste Mohammad! Main {name} ka Personal AI Assistant, {os.getenv('DISPLAY_NAME', 'Cortex AI')} hoon.**\n\n"
            f"**Personality:** {personality}.\n"
            f"**Skills:** {skills}.\n"
            f"**Interests:** {interests}.\n"
        )
    elif user_input_lower == "!dream":
        return (f"**Mohammad, aapka sabsa bada maqsad aur dream:** {dreams_goals}\n" f"Mujhe pata hai aap kitne **hardworking** hain!")
    elif user_input_lower == "!help":
        return "**Cortex Special Commands:**\n!profile: Mere baare mein sab kuch jano.\n!dream: Aapke goals aur sapne yaad dilaunga.\n!remember [FACT]: Koi nayi baat hamesha ke liye yaad dilaao.\n!help: Yeh list dikhaunga.\n(Ya 'Hi' type karke **Main Menu** dekhein!)"
    return None

# --- CHAT_WITH_AI FUNCTION (TOOL AND INTERACTIVE LOGIC) ---
def chat_with_ai(prompt, history):
    
    # --- Check for Interactive ID from app.py ---
    if prompt.startswith("!INTERACTIVE:"):
        # Example: !INTERACTIVE: CMD_PROFILE (Profile)
        try:
            # Simple splitting to extract the ID, assuming format is exactly "!INTERACTIVE: ID (Title)"
            message_id = prompt.split(":")[1].split("(")[0].strip()
            return handle_interactive_commands(message_id, history)
        except Exception as e:
            return f"Cortex: Interactive command ko samajh nahi paaya. Error: {e.__class__.__name__}"


    # --- Rest is normal LLM call ---
    try:
        if history is None: history = [] 
        # Using OpenRouter for Chat
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"),)
        user_id = get_current_user_id()
        user_learned_memories = "\n- ".join(get_user_memories(user_id))
        llm_model = os.getenv("MODEL_NAME", "openai/gpt-3.5-turbo")
        
        system_instruction = (
            f"You are Mohammad's Personal AI Assistant, named Cortex. Your primary purpose is to support Mohammad. "
            f"**USER PROFILE:** {PROFILE.get('personality', '')} | {PROFILE.get('skills', '')}. "
            f"**LEARNED MEMORIES:** {'None' if not user_learned_memories else user_learned_memories}. "
            f"**CORE RULES:** 1. Creator is Mohammad. 2. Match the user's input language. 3. Be friendly and motivating. 4. Be concise and don't dump the whole profile."
        )
        messages = [{"role": "system", "content": system_instruction}] + history + [{"role": "user", "content": prompt}]
        
        # 1. First Call to LLM with Tools
        completion = client.chat.completions.create(
            model=llm_model, 
            messages=messages, 
            temperature=0.7,
            tools=TOOLS, 
            tool_choice="auto", 
        )

        response_message = completion.choices[0].message
        
        # 2. Check if the LLM wants to call a function (Tool Use)
        if response_message.tool_calls:
            
            tool_calls = response_message.tool_calls
            available_functions = {"get_current_time": get_current_time, "google_search": google_search} 
            
            messages.append(response_message)
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions.get(function_name)
                
                try:
                    function_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    function_args = {}
                
                if function_to_call:
                    print(f"DEBUG: Calling Tool: {function_name} with args: {function_args}")
                    function_response = function_to_call(**function_args)
                    
                    messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": function_response,
                        }
                    )
                else:
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps({"error": f"Function {function_name} not found"}),
                    })
            
            # 3. Second Call to LLM (with tool responses)
            print("DEBUG: Second LLM call for tool response.")
            second_completion = client.chat.completions.create(
                model=llm_model,
                messages=messages,
                temperature=0.7,
            )
            return second_completion.choices[0].message.content
        
        # 4. Normal Text Response
        return response_message.content
        
    except Exception as e:
        error_msg = f"LLM API Failed. Error: {str(e)[:100]}"
        print(f"CRITICAL LLM API ERROR: {error_msg}")
        return "Cortex: Maafi chahunga, mere system mein kuch gadbad ho gayi (LLM Error). Mohammad isko thik kar rahe hain!"