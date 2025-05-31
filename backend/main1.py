# main.py
from fastapi import FastAPI
import gradio as gr
from llama_index.indices.managed.llama_cloud import LlamaCloudIndex
from llama_index.llms.groq import Groq  # Correct import path
from dotenv import load_dotenv
import os

load_dotenv('.env.local')

app = FastAPI()

class PDFChatbot:
    def __init__(self):
        self.index = None
        self.llm = None
        self.initialize_services()
        
    def initialize_services(self):
        try:
            # Initialize LlamaCloud
            self.index = LlamaCloudIndex(
                name="gentle-impala-2025-05-01",
                project_name="Default",
                organization_id="37173c96-dff2-47fc-9f72-854c3d98cf31",
                api_key=os.getenv("LLAMA_CLOUD_API_KEY")
            )
            
            # Initialize Groq only if API key exists
            if os.getenv("GROQ_API_KEY"):
                self.llm = Groq(
                    api_key=os.getenv("GROQ_API_KEY"),
                    model="mixtral-8x7b-32768"
                )
                print("Initialized with Groq LLM support")
            else:
                print("Initialized in retrieval-only mode")
                
        except Exception as e:
            raise RuntimeError(f"Initialization error: {str(e)}")

    def chat(self, message, history):
        if not self.index:
            return "System not ready. Check backend logs."
            
        try:
            # Retrieve documents
            retriever = self.index.as_retriever(similarity_top_k=3)
            nodes = retriever.retrieve(message)
            
            # Format context
            context = "\n\n".join(
                f"DOCUMENT {i} (Score: {node.score:.2f}):\n{node.node.get_content()}"
                for i, node in enumerate(nodes, 1)
            )
            
            if self.llm:
                # Enhanced response with Groq
                response = self.llm.complete(
                    f"Context:\n{context}\n\nQuestion: {message}\n"
                    "Answer concisely using only the context. "
                    "If unsure, say 'The documents don't contain this information'."
                )
                return str(response)
            else:
                # Fallback to raw retrieval
                return (
                    "Retrieved documents:\n\n"
                    f"{context}\n\n"
                    "Note: Add GROQ_API_KEY to .env.local for enhanced answers"
                )
                
        except Exception as e:
            return f"Error: {str(e)}"

# Initialize chatbot
chatbot = PDFChatbot()

# Gradio interface
gradio_app = gr.ChatInterface(
    fn=chatbot.chat,
    title="Document Assistant",
    description="Retrieval with optional Groq enhancement",
    examples=[
        "What are the key points?",
        "Explain the main concept",
        "Find technical details about..."
    ]
)

# Mount to FastAPI
app = gr.mount_gradio_app(app, gradio_app, path="/")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "groq_enabled": bool(os.getenv("GROQ_API_KEY"))
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)