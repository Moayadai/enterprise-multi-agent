import sys
import os

# تأمين مسار المشروع
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

# 💡 استدعاء موظفي الشركة (الوكلاء) وأداة الـ HR
from src.agents.hr_agent import hr_node, hr_tools
from src.agents.it_agent import it_node

# 1. تعريف حالة الشركة (State) التي تمر بين الموظفين
class State(TypedDict):
    messages: Annotated[list, add_messages]

# 2. نظام المشرف الذكي (Supervisor Router)
def supervisor_router(state: State) -> Literal["hr_agent", "it_agent"]:
    print("🧠 Supervisor is analyzing the request to assign the right agent...")
    
    # المشرف يمتلك عقله الخاص ليتخذ القرار
    llm = ChatOllama(model="llama3.1", base_url="http://localhost:11434", temperature=0.0)
    user_query = state["messages"][-1].content.lower()
    
    # توجيه المشرف (Prompt)
    supervisor_prompt = f"""You are the routing manager for OuraTech.
    Route the following query to the correct department.
    - Respond with ONLY the word 'HR' if the query is about company policies, vacations, HR, or employees (Moayad).
    - Respond with ONLY the word 'IT' if the query is about math, coding, or general knowledge.
    
    Query: {user_query}"""
    
    response = llm.invoke([SystemMessage(content=supervisor_prompt)])
    decision = response.content.strip().upper()
    
    # توجيه هجين (Hybrid) لضمان دقة 100% مع النماذج المحلية
    hr_keywords = ["ouratech", "moayad", "policy", "أورا", "مؤيد", "اجازة", "سياسة", "hr", "vacation"]
    if "HR" in decision or any(k in user_query for k in hr_keywords):
        print("👔 Assigned to: HR Department")
        return "hr_agent"
    else:
        print("💻 Assigned to: IT Department")
        return "it_agent"

# 3. بناء الهيكل التنظيمي للشركة (Graph)
graph_builder = StateGraph(State)

# إنشاء مكاتب الموظفين
graph_builder.add_node("hr_agent", hr_node)
graph_builder.add_node("it_agent", it_node)

# إنشاء مكتبة ملفات الـ HR (أدوات البحث)
hr_tool_node = ToolNode(tools=hr_tools)
graph_builder.add_node("tools", hr_tool_node) # سميناها tools ليتعرف عليها LangGraph تلقائياً

# 4. رسم خطوط سير العمل بين الأقسام (Edges)
# أ) الطلب يدخل أولاً للمشرف ليقرر أين يذهب
graph_builder.add_conditional_edges(START, supervisor_router)

# ب) مسار قسم الـ IT: يستلم الطلب -> يجاوب -> تنتهي المهمة
graph_builder.add_edge("it_agent", END)

# ج) مسار قسم الـ HR: يستلم الطلب -> قد يستخدم أداة -> يجاوب -> تنتهي المهمة
graph_builder.add_conditional_edges("hr_agent", tools_condition)
graph_builder.add_edge("tools", "hr_agent")

# 5. تجميع الشركة وتفعيل الذاكرة
memory = MemorySaver()
company_app = graph_builder.compile(checkpointer=memory)

if __name__ == "__main__":
    print("🏢 OuraTech Enterprise Multi-Agent Corporation is Online!")
    print("Type 'exit' or 'quit' to leave the company building.\n")
    print("-" * 50)
    
    config = {"configurable": {"thread_id": "ouratech_enterprise_1"}}
    
    while True:
        user_query = input("👤 You: ")
        
        if user_query.lower() in ['exit', 'quit', 'خروج']:
            print("👋 Company shutting down...")
            break
            
        inputs = {"messages": [HumanMessage(content=user_query)]}
        
        # تشغيل الشركة ومراقبة العمليات
        for event in company_app.stream(inputs, config=config, stream_mode="values"):
            message = event["messages"][-1]
            
            if message.type == "ai" and message.tool_calls:
                print(f"🔍 HR is searching records using: {message.tool_calls[0]['name']}...")
            
            elif message.type == "ai" and message.content and not message.tool_calls:
                print(f"\n🎯 Final Answer:\n{message.content}\n")
                print("-" * 50)