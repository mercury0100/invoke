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
)

integrations = [
    "google-contacts",
    "google-tasks",
    "google-calendar",
    "google-gmail-send",
    "youtube"
    ]

invoke = InvokeAgent(llm, integrations)

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