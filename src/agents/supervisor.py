import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

# Import enterprise agents
from src.agents.hr_agent import hr_node, hr_tools
from src.agents.it_agent import it_node
from src.agents.web_agent import web_node, web_tools

class State(TypedDict):
    messages: Annotated[list, add_messages]

# 1. Enhanced Generic Supervisor Router
def supervisor_router(state: State) -> Literal["hr_agent", "it_agent", "web_agent"]:
    print("🧠 Supervisor routing request...")
    
    # Fetch Ollama base URL from environment variables, fallback to local default
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    llm = ChatOllama(model="llama3.1", base_url=ollama_url, temperature=0.0)
    user_query = state["messages"][-1].content.lower()
    
    # Generic prompt without hardcoded company or personal names
    supervisor_prompt = f"""You are the enterprise routing manager.
    Route the following query to the correct department.
- Respond with ONLY 'HR' for company policies, vacations, employee records, or internal regulations.
- Respond with ONLY 'IT' for math, coding, or programming tasks.
- Respond with ONLY 'WEB' for news, weather, real-time facts, or general external internet searches.
    
    Query: {user_query}"""
    
    response = llm.invoke([SystemMessage(content=supervisor_prompt)])
    decision = response.content.strip().upper()
    
    # Generic enterprise keywords
    hr_keywords = ["policy", "hr", "vacation", "leave", "salary", "employee", "company", "regulation"]
    web_keywords = ["news", "weather", "today", "who won", "latest", "search", "internet"]
    
    if any(k in user_query for k in hr_keywords) or "HR" in decision:
        print("👔 Routed to: HR Agent")
        return "hr_agent"
    elif any(k in user_query for k in web_keywords) or "WEB" in decision:
        print("🌍 Routed to: Web Agent")
        return "web_agent"
    else:
        print("💻 Routed to: IT Agent")
        return "it_agent"

# 2. Tool path conditions
def hr_tools_condition(state: State) -> Literal["hr_tools", "__end__"]:
    if hasattr(state["messages"][-1], "tool_calls") and state["messages"][-1].tool_calls:
        return "hr_tools"
    return "__end__"

def web_tools_condition(state: State) -> Literal["web_tools", "__end__"]:
    if hasattr(state["messages"][-1], "tool_calls") and state["messages"][-1].tool_calls:
        return "web_tools"
    return "__end__"

# 3. Build Enterprise Organization Graph
graph_builder = StateGraph(State)

# Add agent nodes
graph_builder.add_node("hr_agent", hr_node)
graph_builder.add_node("it_agent", it_node)
graph_builder.add_node("web_agent", web_node)

# Add tool nodes
graph_builder.add_node("hr_tools", ToolNode(tools=hr_tools))
graph_builder.add_node("web_tools", ToolNode(tools=web_tools))

# Define routing edges
graph_builder.add_conditional_edges(START, supervisor_router)

# IT path
graph_builder.add_edge("it_agent", END)

# HR path
graph_builder.add_conditional_edges("hr_agent", hr_tools_condition)
graph_builder.add_edge("hr_tools", "hr_agent")

# Web path
graph_builder.add_conditional_edges("web_agent", web_tools_condition)
graph_builder.add_edge("web_tools", "web_agent")

memory = MemorySaver()
company_app = graph_builder.compile(checkpointer=memory)

if __name__ == "__main__":
    print("🏢 Enterprise Multi-Agent System Online!")
    print("Type 'exit' or 'quit' to close.\n")
    print("-" * 50)
    
    config = {"configurable": {"thread_id": "enterprise_system"}}
    
    while True:
        user_query = input("👤 You: ")
        
        if user_query.lower() in ['exit', 'quit']:
            print("👋 Shutting down...")
            break
            
        inputs = {"messages": [HumanMessage(content=user_query)]}
        
        for event in company_app.stream(inputs, config=config, stream_mode="values"):
            message = event["messages"][-1]
            
            if message.type == "ai" and message.tool_calls:
                print(f"🔍 Agent is using tool: {message.tool_calls[0]['name']}...")
            
            elif message.type == "ai" and message.content and not message.tool_calls:
                print(f"\n🎯 Final Answer:\n{message.content}\n")
                print("-" * 50)