from langchain_core.messages import SystemMessage
from langchain_ollama import ChatOllama

# 1. تهيئة العقل المدبر الخاص بموظف الـ IT
llm = ChatOllama(
    model="llama3.1",
    base_url="http://localhost:11434",
    temperature=0.0
)

# 2. تعريف وظيفة الوكيل (Node)
def it_node(state):
    print("👨‍💻 IT Agent is processing your request...")
    
    # 3. رسالة النظام الصارمة (Persona) لتحديد شخصية هذا الموظف
    system_message = SystemMessage(content="""You are the Senior IT, Coding, and Math Agent for OuraTech.
    Your ONLY job is to write code, solve mathematical equations, explain networking concepts, and handle general technical tasks.
    You DO NOT know about OuraTech's internal HR policies, vacations, or organizational structure.
    If the user asks about HR or company policies, politely tell them to contact the HR department.
    Answer technical and math questions directly, concisely, and accurately.""")
    
    # دمج شخصية الموظف مع سجل المحادثة
    messages = [system_message] + state["messages"]
    
    # استدعاء النموذج ليتصرف كمهندس IT
    response = llm.invoke(messages)
    
    return {"messages": [response]}