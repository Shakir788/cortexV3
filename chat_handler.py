import json
import os
from openai import OpenAI
import os.path
import requests 
from io import BytesIO 

# Global variable for the profile data
PROFILE = {}
MEMORIES = {}
PROFILE_FILE_PATH = "data/profile.json"
MEMORIES_FILE_PATH = "data/memories.json" 

# --- Final Global Check (Ensure your .env is loaded) ---
WA_ACCESS_TOKEN = os.getenv("WA_ACCESS_TOKEN")
API_URL_MEDIA = "https://graph.facebook.com/v18.0/" 
# --------------------------------------------------------

# --- FINAL IMAGE ANALYSIS FUNCTION ---
def analyze_image(media_id, user_prompt):
    """Downloads image from Meta and analyzes it using GPT-4o (Vision)."""
    
    if not WA_ACCESS_TOKEN:
        return "Cortex: ERROR: Token not loaded for image analysis."

    # Step 1: Get the image file URL from Meta
    media_info_url = f"{API_URL_MEDIA}{media_id}"
    headers = {"Authorization": f"Bearer {WA_ACCESS_TOKEN}"}
    
    try:
        url_response = requests.get(media_info_url, headers=headers, verify=False)
        url_response.raise_for_status()
        media_url = url_response.json().get('url')

        if not media_url:
            return "Cortex: ERROR: Could not retrieve media URL."

        # Step 2: Download the image data
        image_response = requests.get(media_url, headers=headers, verify=False)
        image_response.raise_for_status()
        
        # Step 3: Use a Multi-Modal LLM (GPT-4o) for analysis
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        
        # We need the image link for the LLM to access it
        # NOTE: OpenRouter/GPT-4o can usually access the direct link if provided with the token/header access.
        # Since we cannot host the image, we rely on the LLM to process the direct URL.

        response = client.chat.completions.create(
            model="openai/gpt-4o", # Best model for Vision
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": f"Analyze this image and respond to the user's prompt: {user_prompt}"},
                    {"type": "image_url", "image_url": {"url": media_url, "detail": "high"}},
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


# --- Memory and Profile Load Functions (REST OF THE FILE) ---
# ... (All existing functions like load_memories, load_profile, handle_special_commands, chat_with_ai remain the same)
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
    if user_input_lower.startswith("!remember"):
        memory_to_save = user_input_lower[len("!remember"):].strip()
        if memory_to_save:
            if save_learned_memory(user_id, memory_to_save): 
                return f"Shabaash {name}! Maine yeh baat **hamesha ke liye yaad** kar li hai: '{memory_to_save}'. Ab yeh sirf aapki memory ka hissa hai! 💪"
            return "Arrey! Memory save karne mein kuch gadbad ho gayi."
        return f"{name}, aapko mujhe batana padega ki kya yaad rakhna hai. Jaise: `!remember mera favourite color blue hai`"
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
        return "**Cortex Special Commands:**\n!profile: Mere baare mein sab kuch jano.\n!dream: Aapke goals aur sapne yaad dilaunga.\n!remember [FACT]: Koi nayi baat hamesha ke liye yaad dilaao.\n!help: Yeh list dikhaunga."
    return None
def chat_with_ai(prompt, history):
    try:
        if history is None: history = [] 
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"),)
        user_id = get_current_user_id()
        user_learned_memories = "\n- ".join(get_user_memories(user_id))
        llm_model = os.getenv("MODEL_NAME", "openai/gpt-3.5-turbo")
        system_instruction = (f"You are Mohammad's Personal AI Assistant, named Cortex. Your primary purpose is to support Mohammad. " f"**USER PROFILE:** {PROFILE.get('personality', '')} | {PROFILE.get('skills', '')}. " f"**LEARNED MEMORIES:** {'None' if not user_learned_memories else user_learned_memories}. " f"**CORE RULES:** 1. Creator is Mohammad. 2. Match the user's input language. 3. Be friendly and motivating. 4. Be concise and don't dump the whole profile.")
        messages = [{"role": "system", "content": system_instruction}] + history + [{"role": "user", "content": prompt}]
        completion = client.chat.completions.create(model=llm_model, messages=messages, temperature=0.7,)
        return completion.choices[0].message.content
    except Exception as e:
        error_msg = f"LLM API Failed. Error: {str(e)[:100]}"
        print(f"CRITICAL LLM API ERROR: {error_msg}")
        return "Cortex: Maafi chahunga, mere system mein kuch gadbad ho gayi (LLM Error). Mohammad isko thik kar rahe hain!"
# --- END of chat_handler.py ---