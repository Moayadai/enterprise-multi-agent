import os
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_ollama import ChatOllama

# Import enterprise knowledge tool
from src.tools.knowledge_tool import company_knowledge_search

# Load environment variables
load_dotenv()

# Initialize HR agent model with environment variable support
ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
llm = ChatOllama(
    model="llama3.1",
    base_url=ollama_url,
    temperature=0.0
)

# Bind HR tools
hr_tools = [company_knowledge_search]
hr_llm = llm.bind_tools(hr_tools)

def hr_node(state):
    print("👨‍💼 HR Agent is processing your request...")
    
    # Generic enterprise HR persona
    system_message = SystemMessage(content="""You are the HR and Internal Policies Agent for the enterprise system.
    Your ONLY job is to answer questions about company vacation policies, corporate structure, employee records, and internal HR rules.
    ALWAYS use the company_knowledge_search tool to find accurate information.
    If the user asks about coding, IT, or math, politely tell them that this is not your department.""")
    
    messages = [system_message] + state["messages"]
    response = hr_llm.invoke(messages)
    
    return {"messages": [response]}