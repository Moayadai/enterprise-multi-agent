import os
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_ollama import ChatOllama
from langchain_core.tools import tool

# Load environment variables
load_dotenv()

@tool
def wikipedia_search_tool(query: str) -> str:
    """Searches Wikipedia for facts, history, science, technology, and general knowledge."""
    from langchain_community.tools import WikipediaQueryRun
    from langchain_community.utilities import WikipediaAPIWrapper
    
    print(f"🌍 Searching Wikipedia for: {query}")
    api_wrapper = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=1000)
    search = WikipediaQueryRun(api_wrapper=api_wrapper)
    
    try:
        return search.invoke(query)
    except Exception as e:
        return f"Could not find information on Wikipedia for {query}."

# Fetch Ollama base URL from environment variables
ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

llm = ChatOllama(
    model="llama3.1",
    base_url=ollama_url,
    temperature=0.0
)

web_tools = [wikipedia_search_tool]
web_llm = llm.bind_tools(web_tools)

def web_node(state):
    print("🌍 External Research Agent is analyzing the request...")
    
    # Generic enterprise system message
    system_message = SystemMessage(content="""You are the External Research Agent for the enterprise system.
    Your ONLY job is to search for external knowledge (like technology history, general facts, etc.) using the wikipedia_search_tool.
    ALWAYS use the tool before answering. Summarize the findings concisely.""")
    
    messages = [system_message] + state["messages"]
    response = web_llm.invoke(messages)
    
    return {"messages": [response]}