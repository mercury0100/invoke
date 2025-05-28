from langchain_openai import ChatOpenAI
from invoke_agent.agent import InvokeAgent
from dotenv import load_dotenv
import os

load_dotenv()  # This loads variables from the .env file
openai_key = os.getenv("OPENAI_API_KEY")

# Initialize LLM and InvokeExecutor
llm = ChatOpenAI(
    model="gpt-4.1",
    openai_api_key=openai_key,
    #temperature=0.1,  # Balances creativity & coherence
    #max_tokens=5000   # Adjust as needed
)

integrations = [
    "open-meteo",
    "open-weather-map",
    "google-directions",
    "google-places",
    "google-calendar", # 2 failures - bad examples
    "google-gmail", # 4 failures - Bad examples
    #"google-tasks", # ???
    #"google-contacts", # ???
    #"google-drive", # ???
    #"youtube", # 2 failures - bad examples
    #"microsoft-outlook", # 2 failures - Bad examples
    #"microsoft-calendar", # 2 failures - Bad examples
    #"microsoft-onenote",
    "spotify", # 4 failures - no premium
    #"calendly", # No account
    ]

invoke = InvokeAgent(llm, integrations, verbose=False)

# Start interactive loop
print("\n🤖 Invoke Chat Agent is running. Type your request below.")
print("Type 'exit' or 'quit' to stop.\n")

while True:
    user_input = input("📝 You: ").strip()

    if user_input.lower() in ["exit", "quit"]:
        print("\n👋 Exiting Invoke Chat Agent. Goodbye!")
        break  # Exit the loop
    
    print('\n💡 Thinking very hard...')

    final_response = invoke.chat(user_input)
    print(final_response)