from langchain_core.messages import SystemMessage
from langchain_ollama import ChatOllama

# استدعاء أداة البحث المؤسسية
from src.tools.knowledge_tool import company_knowledge_search

# 1. تهيئة العقل المدبر الخاص بموظف الـ HR
llm = ChatOllama(
    model="llama3.1",
    base_url="http://localhost:11434",
    temperature=0.0
)

# 2. تسليح موظف الـ HR بأداة البحث
hr_tools = [company_knowledge_search]
hr_llm = llm.bind_tools(hr_tools)

# 3. تعريف وظيفة الوكيل (Node)
def hr_node(state):
    print("👨‍💼 HR Agent is processing your request...")
    
    # 4. رسالة النظام الصارمة (Persona) لتحديد شخصية هذا الموظف
    system_message = SystemMessage(content="""You are the HR and Internal Policies Agent for OuraTech.
    Your ONLY job is to answer questions about OuraTech's vacation policies, company structure, employees (like Moayad), and HR rules.
    ALWAYS use the company_knowledge_search tool to find accurate information.
    If the user asks about coding, IT, or math, politely tell them that this is not your department.""")
    
    # دمج شخصية الموظف مع سجل المحادثة
    messages = [system_message] + state["messages"]
    
    # استدعاء النموذج ليتصرف كـ HR
    response = hr_llm.invoke(messages)
    
    return {"messages": [response]}