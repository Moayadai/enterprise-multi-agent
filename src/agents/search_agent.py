import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Append project root for correct imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from src.tools.knowledge_tool import company_knowledge_search

# 1. Define system state
class State(TypedDict):
    messages: Annotated[list, add_messages]

# 2. Initialize LLM with environment variable support
ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
llm = ChatOllama(
    model="llama3.1",
    base_url=ollama_url,
    temperature=0.0 
)

hr_tools = [company_knowledge_search]

# 3. Define agent nodes
def hr_node(state: State):
    print("🤖 HR Agent is thinking...")
    
    user_text = state["messages"][-1].content.lower()
    # Generic enterprise keywords
    enterprise_keywords = ['policy', 'vacation', 'company', 'hr', 'structure', 'employee', 'salary', 'regulation', 'leave']
    
    if any(keyword in user_text for keyword in enterprise_keywords):
        llm_to_use = llm.bind_tools(hr_tools)
    else:
        llm_to_use = llm

    # Generic enterprise system prompt
    system_prompt = SystemMessage(content="""You are an intelligent enterprise HR assistant.
    CRITICAL RULES:
    1. For general knowledge or math questions, ANSWER DIRECTLY and CONCISELY.
    2. For company policies, HR regulations, or structure, USE the company_knowledge_search tool.
    3. Never explain your thought process. Just provide the final answer.
    4. If you use the search tool, USE IT ONLY ONCE per question. Do not search multiple times.""")
    
    messages_to_pass = [system_prompt] + state["messages"]
        
    return {"messages": [llm_to_use.invoke(messages_to_pass)]}

hr_tool_node = ToolNode(tools=hr_tools)

# 4. Build graph architecture
graph_builder = StateGraph(State)

graph_builder.add_node("hr_agent", hr_node)
graph_builder.add_node("hr_tools", hr_tool_node)

graph_builder.add_edge(START, "hr_agent")
graph_builder.add_conditional_edges("hr_agent", tools_condition)
graph_builder.add_edge("hr_tools", "hr_agent")

# 5. Compile graph with memory saver
memory = MemorySaver()
hr_app = graph_builder.compile(checkpointer=memory)

if __name__ == "__main__":
    print("✅ Enterprise HR Multi-Agent System with Memory is Online!")
    print("Type 'exit' or 'quit' to end the conversation.\n")
    print("-" * 50)
    
    config = {"configurable": {"thread_id": "enterprise_session_1"}}
    
    while True:
        user_query = input("👤 You: ")
        
        if user_query.lower() in ['exit', 'quit']:
            print("👋 System shutting down...")
            break
            
        inputs = {"messages": [HumanMessage(content=user_query)]}
        
        for event in hr_app.stream(inputs, config=config, stream_mode="values"):
            message = event["messages"][-1]
            
            if message.type == "ai" and message.tool_calls:
                print(f"🛠️  Agent is searching using: {message.tool_calls[0]['name']}...")
            
            elif message.type == "ai" and message.content and not message.tool_calls:
                print(f"\n🎯 Final Answer:\n{message.content}\n")
                print("-" * 50)