from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_index.indices.managed.llama_cloud import LlamaCloudIndex
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv('.env.local')

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    sources: list = []

class DocumentChat:
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
            print(f"Error initializing index: {str(e)}")
            raise

    async def get_response(self, query: str) -> dict:
        try:
            # Get relevant documents
            retriever = self.index.as_retriever(similarity_top_k=3)
            nodes = retriever.retrieve(query)
            
            # Format response
            sources = []
            for node in nodes:
                sources.append({
                    "content": node.node.get_content(),
                    "score": float(node.score)
                })
            
            # Get response from query engine
            response = self.index.as_query_engine().query(query)
            
            return {
                "response": str(response),
                "sources": sources
            }
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "sources": []
            }

# Initialize chat
chat = DocumentChat()

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        result = await chat.get_response(request.message)
        return ChatResponse(**result)
    except Exception as e:
        return ChatResponse(
            response=f"Error processing request: {str(e)}",
            sources=[]
        )

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)