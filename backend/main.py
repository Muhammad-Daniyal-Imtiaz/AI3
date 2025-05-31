# main.py
from fastapi import FastAPI
import gradio as gr
from llama_index.indices.managed.llama_cloud import LlamaCloudIndex
from dotenv import load_dotenv
import os

load_dotenv('.env.local')

app = FastAPI()

class PDFChatbot:
    def __init__(self):
        self.index = None
        self.initialize_index()
        
    def initialize_index(self):
        try:
            self.index = LlamaCloudIndex(
                name="gentle-impala-2025-05-01",
                project_name="Default",
                organization_id="37173c96-dff2-47fc-9f72-854c3d98cf31",
                api_key=os.getenv("LLAMA_CLOUD_API_KEY")
            )
            print("Index initialized successfully")
        except Exception as e:
            raise RuntimeError(f"Error initializing index: {str(e)}")

    def chat(self, message, history):
        if not self.index:
            return "System not ready. Please check backend logs."
        try:
            # Use only retrieval without LLM
            retriever = self.index.as_retriever(
                similarity_top_k=3  # Retrieve top 3 most relevant chunks
            )
            retrieved_nodes = retriever.retrieve(message)
            
            # Format the raw retrieved content
            response = "Retrieved information:\n\n"
            for i, node in enumerate(retrieved_nodes, 1):
                response += f"--- Result {i} (Score: {node.score:.2f}) ---\n"
                response += f"{node.node.get_content()}\n\n"
            
            return response
        except Exception as e:
            return f"Error: {str(e)}"

# Initialize chatbot
chatbot = PDFChatbot()

# Create Gradio app
gradio_app = gr.ChatInterface(
    fn=chatbot.chat,
    title="PDF Document Retrieval",
    description="This system retrieves relevant passages from your documents without generative AI.",
    examples=[
        "What are the key findings?",
        "Show me information about...",
        "Find relevant passages regarding..."
    ]
)

# Mount Gradio app
app = gr.mount_gradio_app(app, gradio_app, path="/")

# FastAPI route
@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)