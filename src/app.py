import streamlit as st
import sys
import os
import pypdf
from langchain_core.messages import HumanMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

# Append project root for LangGraph supervisor
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.agents.supervisor import company_app

st.set_page_config(page_title="Enterprise AI", page_icon="✨", layout="centered")

# UI styling (Smart RTL/LTR & component hiding)
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden !important;}
    
    /* Smart text and RTL support */
    .stApp, .stMarkdown, p, h1, h2, h3, div, ul, ol, li {
        unicode-bidi: plaintext !important;
        text-align: start !important;
        font-family: 'Segoe UI', Tahoma, sans-serif !important;
    }
    
    /* RTL list padding */
    ul, ol {
        direction: rtl !important;
        padding-right: 2rem !important; 
    }
    li {
        text-align: right !important;
        direction: rtl !important;
    }
    
    /* Keep code blocks LTR */
    pre, code {
        direction: ltr !important;
        text-align: left !important;
    }
    </style>
""", unsafe_allow_html=True)

# 1. Initialize session state
if "processing" not in st.session_state:
    st.session_state.processing = False
if "pending_process" not in st.session_state:
    st.session_state.pending_process = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "temp_vector_store" not in st.session_state:
    st.session_state.temp_vector_store = None
if "uploaded_filename" not in st.session_state:
    st.session_state.uploaded_filename = ""

# 2. Sidebar (Temp RAG Document Processing)
with st.sidebar:
    st.markdown("<h3 style='text-align: center;'>📎 Attachments</h3>", unsafe_allow_html=True)
    st.caption("Temporary session files. Cleared on exit.")
    
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    
    if uploaded_file is not None:
        if st.session_state.uploaded_filename != uploaded_file.name:
            with st.spinner("🔄 Indexing document..."):
                try:
                    pdf_reader = pypdf.PdfReader(uploaded_file)
                    text = ""
                    for page in pdf_reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += extracted + "\n"
                    
                    # Chunking for optimization
                    text_splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)
                    chunks = text_splitter.split_text(text)
                    
                    # Embeddings and in-memory store
                    embeddings = OllamaEmbeddings(model="nomic-embed-text")
                    st.session_state.temp_vector_store = Chroma.from_texts(chunks, embeddings)
                    st.session_state.uploaded_filename = uploaded_file.name
                    
                    st.success("✅ Document indexed successfully.")
                except Exception as e:
                    st.error(f"Error processing file: {e}")

# 3. Header
st.markdown("<h1 style='text-align: center; direction: ltr;'>✨ Enterprise AI</h1>", unsafe_allow_html=True)
st.caption("<div style='text-align: center;'>Official Workspace</div>", unsafe_allow_html=True)

# 4. Chat history
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "✨"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 5. Input field & concurrency lock
prompt = st.chat_input("Type a message or query the document...", disabled=st.session_state.processing)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.processing = True
    st.session_state.pending_process = True
    st.rerun()

# 6. Request processing & LangGraph routing
if st.session_state.pending_process:
    last_user_message = st.session_state.messages[-1]["content"]
    full_query = last_user_message
    
    # Search in temp document if available
    if st.session_state.temp_vector_store is not None:
        relevant_docs = st.session_state.temp_vector_store.similarity_search(last_user_message, k=3)
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        full_query = f"Extracted context from attached document:\n\n{context}\n\nBased on this context, answer the user's request: {last_user_message}"

    config = {"configurable": {"thread_id": "enterprise_file_upload"}}
    inputs = {"messages": [HumanMessage(content=full_query)]}
    
    with st.spinner("Processing..."):
        final_response = ""
        for event in company_app.stream(inputs, config=config, stream_mode="values"):
            message = event["messages"][-1]
            if message.type == "ai" and message.content and not message.tool_calls:
                final_response = message.content
        
        if final_response:
            st.session_state.messages.append({"role": "assistant", "content": final_response})
            
    st.session_state.pending_process = False
    st.session_state.processing = False
    st.rerun()