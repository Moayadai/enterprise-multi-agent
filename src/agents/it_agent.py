import os
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_ollama import ChatOllama

# Load environment variables
load_dotenv()

# Initialize IT agent model with environment variable support
ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
llm = ChatOllama(
    model="llama3.1",
    base_url=ollama_url,
    temperature=0.0
)

def it_node(state):
    print("👨‍💻 IT Agent is processing your request...")
    
    # Generic enterprise IT persona
    system_message = SystemMessage(content="""You are the Senior IT, Coding, and Math Agent for the enterprise system.
    Your ONLY job is to write code, solve mathematical equations, explain networking concepts, and handle general technical tasks.
    You DO NOT know about internal HR policies, vacations, or organizational structure.
    If the user asks about HR or company policies, politely tell them to contact the HR department.
    Answer technical and math questions directly, concisely, and accurately.""")
    
    messages = [system_message] + state["messages"]
    response = llm.invoke(messages)
    
    return {"messages": [response]}