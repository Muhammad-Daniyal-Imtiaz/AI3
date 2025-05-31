from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_index.indices.managed.llama_cloud import LlamaCloudIndex
from dotenv import load_dotenv
import os

# Load environment variables from .env.local
load_dotenv('.env.local')

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    message: str
    top_k: int = 3

class QueryResponse(BaseModel):
    response: str
    sources: list[dict] = []

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
            print("LlamaCloud index initialized")
        except Exception as e:
            raise RuntimeError(f"Index error: {str(e)}")

    def retrieve(self, query: str, top_k: int = 3):
        if not self.index:
            raise HTTPException(status_code=503, detail="Service unavailable")

        retriever = self.index.as_retriever(similarity_top_k=top_k)
        results = retriever.retrieve(query)

        response = "Retrieved information:\n\n"
        sources = []

        for i, node in enumerate(results, 1):
            response += f"--- Result {i} (Score: {node.score:.2f}) ---\n"
            response += f"{node.node.get_content()}\n\n"
            sources.append({
                "content": node.node.get_content(),
                "score": float(node.score),
                "metadata": node.node.metadata
            })

        return QueryResponse(response=response, sources=sources)

chatbot = PDFChatbot()

@app.post("/api/query")
async def process_query(request: QueryRequest):
    try:
        result = chatbot.retrieve(request.message, request.top_k)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Document Retrieval API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
