from langchain_core.tools import tool
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

# 1. Initialize the embeddings model
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)

# 2. Connect to the local vector database
vector_store = Chroma(
    persist_directory="./chroma_db_storage", 
    embedding_function=embeddings
)

# 3. Configure the retriever to fetch the top 2 results
retriever = vector_store.as_retriever(search_kwargs={"k": 2})

# 4. Build the tool manually (Best architectural practice for LangGraph)
# 4. Build the tool manually (Best architectural practice for LangGraph)
@tool
def company_knowledge_search(query: str) -> str:
    """Use this tool ONLY to search for OuraTech company policies, HR rules, IT security, and organizational structure. 
    CRITICAL: DO NOT use this tool for general knowledge, coding, or math questions (like 1+1)."""
    # Search the vector database
    docs = retriever.invoke(query)
    # Combine the extracted documents into a single string for the LLM
    return "\n\n".join([doc.page_content for doc in docs])

if __name__ == "__main__":
    print("✅ Search tool initialized successfully (using @tool)!")
    
    # Quick standalone test
    print("\n🔄 Testing the tool for 'vacation'...")
    test_result = company_knowledge_search.invoke("vacation policy")
    print("🔍 Search Result:")
    print(f"   {test_result}")