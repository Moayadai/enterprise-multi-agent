import sys
import os

# إضافة مسار المشروع لتجنب أخطاء الاستيراد
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
# 💡 الاستدعاء الجديد: مكتبة الذاكرة من LangGraph
from langgraph.checkpoint.memory import MemorySaver

from src.tools.knowledge_tool import company_knowledge_search

# 1. تعريف حالة النظام (State)
class State(TypedDict):
    messages: Annotated[list, add_messages]

# 2. تهيئة العقل المدبر
llm = ChatOllama(
    model="llama3.1",
    base_url="http://localhost:11434",
    temperature=0.0 
)

tools = [company_knowledge_search]

# 3. تعريف العقد (Nodes)
def agent_node(state: State):
    print("🤖 Agent is thinking...")
    
    user_text = state["messages"][-1].content.lower()
    company_keywords = ['ouratech', 'policy', 'vacation', 'moayad', 'company', 'hr', 'structure', 'أورا', 'سياسة', 'مؤيد', 'اجازة']
    
    if any(keyword in user_text for keyword in company_keywords):
        llm_to_use = llm.bind_tools(tools)
    else:
        llm_to_use = llm

    # 💡 تعديل معماري: حقن رسالة النظام داخل العقدة فقط لتوفير استهلاك الذاكرة (Tokens)
    system_prompt = SystemMessage(content="""You are OuraTech's intelligent AI assistant.
    CRITICAL RULES:
    1. For general knowledge or math questions, ANSWER DIRECTLY and CONCISELY.
    2. For OuraTech policies, HR, or structure, USE the company_knowledge_search tool.
    3. Never explain your thought process. Just provide the final answer.
    4. If you use the search tool, USE IT ONLY ONCE per question. Do not search multiple times.""")
    
    # دمج رسالة النظام مع تاريخ المحادثة المحفوظ
    messages_to_pass = [system_prompt] + state["messages"]
        
    return {"messages": [llm_to_use.invoke(messages_to_pass)]}

tool_node = ToolNode(tools=tools)

# 4. بناء المسار المعماري (Graph)
graph_builder = StateGraph(State)

graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "agent")
graph_builder.add_conditional_edges("agent", tools_condition)
graph_builder.add_edge("tools", "agent")

# 💡 5. تهيئة الذاكرة (Memory) وتجميع النظام
memory = MemorySaver()
# نمرر الذاكرة كـ checkpointer للنظام ليحفظ المحادثات
agent_app = graph_builder.compile(checkpointer=memory)

if __name__ == "__main__":
    print("✅ The OuraTech Multi-Agent System with MEMORY is Online!")
    print("Type 'exit' or 'quit' to end the conversation.\n")
    print("-" * 50)
    
    # 💡 إعداد معرّف الجلسة (Thread ID). كل مستخدم أو محادثة يكون لها رقم خاص
    config = {"configurable": {"thread_id": "ouratech_session_1"}}
    
    while True:
        user_query = input("👤 You: ")
        
        if user_query.lower() in ['exit', 'quit', 'خروج']:
            print("👋 System shutting down...")
            break
            
        # 💡 نرسل رسالة المستخدم فقط (بدون رسالة النظام لأنها تُحقن تلقائياً في الأعلى)
        inputs = {"messages": [HumanMessage(content=user_query)]}
        
        # تمرير الـ config ليعرف النظام أي ذاكرة يستدعي
        for event in agent_app.stream(inputs, config=config, stream_mode="values"):
            message = event["messages"][-1]
            
            if message.type == "ai" and message.tool_calls:
                print(f"🛠️  Agent is searching using: {message.tool_calls[0]['name']}...")
            
            elif message.type == "ai" and message.content and not message.tool_calls:
                print(f"\n🎯 Final Answer:\n{message.content}\n")
                print("-" * 50)