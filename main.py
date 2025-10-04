import os
from chat_handler import chat_with_ai, handle_special_commands
import os.path
from dotenv import load_dotenv # <--- Ye line zaroori hai

load_dotenv() # <--- Aur ye line bhi zaroori hai

def main():
    """Main function to run the Cortex AI chat loop."""
    
    # Initialize the chat history inside main() to fix the error
    history = [] 

    # Load profile name for the prompt
    profile_name = "Mohammad"
    # Note: os.getenv will now correctly read from the .env file after load_dotenv()
    if os.getenv('PROFILE_NAME'):
        profile_name = os.getenv('PROFILE_NAME')
    
    
    print("----------------------------------------------------------------------")
    print("Cortex: Aapka Personal AI Assistant. Online hoon, Mohammad!")
    print("Commands ke liye '!help' type karein. Exit karne ke liye 'exit' type karein.")
    print("----------------------------------------------------------------------")

    while True:
        try:
            # Get user input
            user_input = input(f"{profile_name}: ")
            
            if user_input.lower() == 'exit':
                print("Cortex: Alvida! Aapka khayal rakhna. Main hamesha yahin hoon.")
                break
            
            if not user_input.strip():
                continue

            # 1. Check for special commands
            special_command_response = handle_special_commands(user_input)
            if special_command_response:
                print(f"Cortex: {special_command_response}")
                continue # Skip API call for commands

            # 2. Process normal chat
            
            # Get AI response
            ai_response = chat_with_ai(user_input, history)
            
            # Print response
            print(f"Cortex: {ai_response}")
            
            # 3. Update history for context (important for smooth conversation)
            # User's message
            history.append({"role": "user", "content": user_input})
            # AI's response
            history.append({"role": "assistant", "content": ai_response})
            
            # Keep history short (last 6 turns, for example) to save tokens/cost
            if len(history) > 12: 
                history = history[-10:] # Keep last 10 messages

        except KeyboardInterrupt:
            print("\nCortex: Chat band kar raha hoon. Milte hain!")
            break
        except Exception as e:
            print(f"Cortex: Ek unexpected error aa gaya (System: {e})")
            break

if __name__ == "__main__":
    main()