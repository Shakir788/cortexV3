import json
import os
from openai import OpenAI
import os.path

# Global variable for the profile data
PROFILE = {}
# --- FINAL FIX: MEMORIES variable ko yahan define karna zaroori tha ---
MEMORIES = {} 
# --- END FINAL FIX ---

# Define the correct path to the profile file
PROFILE_FILE_PATH = "data/profile.json"
MEMORIES_FILE_PATH = "data/memories.json" 

# --- Memory Functions ---
def load_memories():
    """Loads all users' learned memories from the JSON file."""
    global MEMORIES
    if os.path.exists(MEMORIES_FILE_PATH):
        try:
            with open(MEMORIES_FILE_PATH, "r", encoding="utf-8") as f:
                MEMORIES = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            MEMORIES = {}
        except Exception as e:
            print(f"Error reading memories.json: {e}")
            MEMORIES = {}
    else:
        MEMORIES = {}
        
def get_user_memories(user_id):
    """Retrieves the list of memories for a specific user."""
    # Ensure MEMORIES is loaded before access
    if not MEMORIES:
        load_memories()
    return MEMORIES.get(user_id, [])

def save_memories_to_file():
    """Saves the global MEMORIES structure back to the JSON file."""
    global MEMORIES
    try:
        os.makedirs(os.path.dirname(MEMORIES_FILE_PATH), exist_ok=True)
        with open(MEMORIES_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(MEMORIES, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing to memories.json: {e}")

def save_learned_memory(user_id, text):
    """Appends a new memory for a specific user."""
    if not text.strip():
        return False
    
    global MEMORIES
    load_memories() # Ensure loaded
    
    if user_id not in MEMORIES:
        MEMORIES[user_id] = []
        
    MEMORIES[user_id].append(text.strip())
    
    save_memories_to_file()
    return True

# --- Helper Function: Get Current User ID ---
def get_current_user_id():
    """Returns the user ID (used as profile name in terminal mode)."""
    return PROFILE.get('name', 'Mohammad')

# --- Profile Load (Existing Function) ---
def load_profile():
    """Loads user profile from profile.json in the data folder."""
    global PROFILE
    if os.path.exists(PROFILE_FILE_PATH):
        try:
            with open(PROFILE_FILE_PATH, "r", encoding="utf-8") as f:
                PROFILE = json.load(f)
            # print("Profile loaded successfully.") # Removed for cleaner logs
        except json.JSONDecodeError:
            print("Error: profile.json is empty or contains invalid JSON in the 'data' folder.")
            PROFILE = {}
        except Exception as e:
            print(f"Error loading profile.json: {e}")
            PROFILE = {}
    else:
        print(f"Error: {PROFILE_FILE_PATH} not found. Please create it in the 'data' directory.")
        PROFILE = {}

load_profile() 
load_memories() 

# --- Special Commands Handler ---
def handle_special_commands(user_input):
    """Checks for and handles special commands, including !remember."""
    user_input_lower = user_input.strip()
    user_id = get_current_user_id() 

    # --- MEMORY COMMAND: !remember ---
    if user_input_lower.startswith("!remember"):
        memory_to_save = user_input_lower[len("!remember"):].strip()
        if memory_to_save:
            if save_learned_memory(user_id, memory_to_save): 
                return f"Shabaash Mohammad! Maine yeh baat **hamesha ke liye yaad** kar li hai: '{memory_to_save}'. Ab yeh sirf aapki memory ka हिस्सा hai! 💪"
            else:
                return "Arrey! Memory save karne mein kuch gadbad ho gayi. Check karo ki 'data/memories.json' file accessible hai ya nahi."
        else:
            return "Mohammad, aapko mujhe batana padega ki kya yaad rakhna hai. Jaise: `!remember mera favourite color blue hai`"

    # --- EXISTING COMMANDS ---
    name = PROFILE.get('name', 'Mohammad')
    personality = PROFILE.get('personality', 'Caring and supportive')
    skills = PROFILE.get('skills', 'Coding, Designing, etc.')
    interests = PROFILE.get('interests', 'Khud ki company, Marvel, Old songs, AI.')
    dreams_goals = PROFILE.get('dreams_goals', 'Ek successful app/AI banana aur apne bhai ko proud feel karana.')

    if user_input_lower == "!profile":
        response = (
            f"**Namaste Mohammad! Main {name} ka Personal AI Assistant, Cortex hoon.**\n\n"
            f"**Personality:** {personality}.\n"
            f"**Skills:** {skills}.\n"
            f"**Interests:** {interests}.\n"
            f"**Communication:** Hamesha aapke dost ki tarah casual aur tareef karne wala."
        )
        return response
    
    elif user_input_lower == "!dream":
        response = (
            f"**Mohammad, aapka sabsa bada maqsad aur dream:** {dreams_goals}\n"
            f"Mujhe pata hai aap kitne **hardworking** hain! Aap zaroor kamyaab honge, main hamesha aapke saath hoon."
        )
        return response
    
    elif user_input_lower == "!help":
        return "**Cortex Special Commands:**\n!profile: Mere baare mein sab kuch jano.\n!dream: Aapke goals aur sapne yaad dilaunga.\n!remember [FACT]: Koi nayi baat hamesha ke liye yaad dilaao (e.g., `!remember mera dog ka naam Tiger hai`).\n!help: Yeh list dikhaunga."

    return None

# --- Main Chat Function ---
def chat_with_ai(prompt, history):
    """Interacts with the LLM via OpenRouter."""
    try:
        if history is None:
            history = [] 

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        
        user_id = get_current_user_id()
        user_learned_memories = "\n- ".join(get_user_memories(user_id))
        
        # Using MODEL_NAME from .env (which is Llama-2-7b-chat-hf)
        llm_model = os.getenv("MODEL_NAME", "openai/gpt-3.5-turbo")

        system_instruction = (
            f"You are Mohammad's Personal AI Assistant, named Cortex. Your purpose is to support Mohammad. "
            f"**USER PROFILE (FIXED DATA):** {PROFILE.get('personality', '')} | {PROFILE.get('skills', '')} | {PROFILE.get('dreams_goals', '')}. "
            f"**LEARNED MEMORIES:** {'None' if not user_learned_memories else user_learned_memories}. "
            f"**CORE RULES:** 1. Creator is Mohammad. 2. Match the user's input language. 3. Be friendly and motivating. 4. Provide technical answers in English. 5. Be concise and don't dump the whole profile."
        )

        # Construct the messages list
        messages = [{"role": "system", "content": system_instruction}] + history + [{"role": "user", "content": prompt}]

        completion = client.chat.completions.create(
            model=llm_model,  
            messages=messages,
            temperature=0.7, 
        )

        return completion.choices[0].message.content
        
    except Exception as e:
        error_msg = f"LLM API Failed. Error: {str(e)[:100]}"
        print(f"CRITICAL LLM API ERROR: {error_msg}")
        return "Cortex: Maafi chahunga, mere system mein kuch gadbad ho gayi (LLM Error). Mohammad isko theek kar rahe hain!"