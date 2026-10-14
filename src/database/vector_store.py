import os
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

# Local directory for vector storage
DB_DIR = "./chroma_db_storage"

# Initialize embeddings
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)

def init_and_seed_db():
    print("🔄 Initializing Vector Database (ChromaDB)...")
    
    # Dummy Corporate Data in English
    documents = [
        "Leave Policy: Employees at OuraTech are entitled to 30 days of paid annual leave.",
        "IT Security: It is strictly forbidden to share passwords or use external cloud servers to upload OuraTech source code.",
        "Organizational Structure: Engineer Moayad Al-Shameri is the Founder and Chief AI Systems Architect of OuraTech."
    ]
    
    # Metadata for source tracking
    metadatas = [{"source": "HR_Policy"}, {"source": "IT_Security"}, {"source": "Company_Structure"}]
    
    try:
        vector_store = Chroma.from_texts(
            texts=documents,
            embedding=embeddings,
            metadatas=metadatas,
            persist_directory=DB_DIR
        )
        print("✅ Database created and documents vectorized successfully!")
        print(f"📁 Storage Path: {DB_DIR}")
        return vector_store
    except Exception as e:
        print(f"❌ Error building database: {e}")

if __name__ == "__main__":
    init_and_seed_db()