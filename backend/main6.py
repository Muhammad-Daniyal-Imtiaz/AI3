# main.py
from fastapi import FastAPI
import gradio as gr
from dotenv import load_dotenv
import os
from composio import ComposioToolSet, App
from typing import List, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv('.env.local')

app = FastAPI()

class GitHubProjectFetcher:
    def __init__(self):
        try:
            api_key = os.getenv("COMPOSIO_API_KEY")
            if not api_key:
                raise ValueError("COMPOSIO_API_KEY not found in environment variables")
                
            self.toolset = ComposioToolSet(api_key=api_key)
            logger.info("ComposioToolSet initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GitHubProjectFetcher: {str(e)}")
            raise
        
    def get_github_projects(self) -> List[str]:
        """Fetch all GitHub repository names for connected accounts"""
        try:
            logger.info("Fetching connected accounts...")
            connections = self.toolset.get_connected_accounts()
            
            if not connections:
                logger.warning("No connected accounts found")
                return []
            
            projects = []
            logger.info(f"Found {len(connections)} connections")
            
            for connection in connections:
                if connection.app == App.GITHUB:
                    logger.info(f"Processing GitHub connection: {connection.account_id}")
                    
                    try:
                        repos = self.toolset.execute_action(
                            app=App.GITHUB,
                            action="list_repos",
                            params={},
                            account_id=connection.account_id
                        )
                        if repos and isinstance(repos, list):
                            projects.extend([repo["name"] for repo in repos])
                            logger.info(f"Found {len(repos)} repositories for account {connection.account_id}")
                        else:
                            logger.warning(f"No repositories returned for account {connection.account_id}")
                    except Exception as e:
                        logger.error(f"Error fetching repos for account {connection.account_id}: {str(e)}")
                        continue
            
            return projects
        except Exception as e:
            logger.error(f"Error in get_github_projects: {str(e)}")
            return []

class GitHubChatbot:
    def __init__(self):
        try:
            self.github_fetcher = GitHubProjectFetcher()
            logger.info("GitHubChatbot initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GitHubChatbot: {str(e)}")
            self.github_fetcher = None

    def chat(self, message: str, history: Optional[list]) -> str:
        try:
            if not self.github_fetcher:
                return "Error: GitHub integration not initialized. Please check server logs."
                
            if any(cmd in message.lower() for cmd in ["list github projects", "show my repositories", "show repos"]):
                projects = self.github_fetcher.get_github_projects()
                
                if not projects:
                    return "No GitHub projects found. Please ensure:\n1. Your GitHub account is connected in Composio\n2. You have repositories in your account\n3. The COMPOSIO_API_KEY is valid"
                
                return "GitHub Projects:\n- " + "\n- ".join(projects)
                
            return ("I can help you list your GitHub projects. Try asking:\n"
                   "- 'list github projects'\n"
                   "- 'show my repositories'\n\n"
                   "Make sure your GitHub account is connected in Composio.")
                   
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            return f"An error occurred: {str(e)}. Please check server logs."

# Initialize chatbot
try:
    chatbot = GitHubChatbot()
    logger.info("Application initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize application: {str(e)}")
    chatbot = None

# Create Gradio app
def get_gradio_app():
    if not chatbot:
        return gr.ChatInterface(
            fn=lambda x,y: "System initialization failed. Check server logs.",
            title="GitHub Projects Viewer - ERROR",
            description="System failed to initialize. Check server logs."
        )
    
    return gr.ChatInterface(
        fn=chatbot.chat,
        title="GitHub Projects Viewer",
        description=(
            "This system connects to your GitHub account via Composio MCP to list your repositories.\n"
            "Make sure your GitHub account is connected in Composio first."
        ),
        examples=[
            "List my GitHub projects",
            "Show my repositories",
            "What projects do I have on GitHub?"
        ]
    )

gradio_app = get_gradio_app()

# Mount Gradio app
app = gr.mount_gradio_app(app, gradio_app, path="/")

# FastAPI routes
@app.get("/health")
def health_check():
    status = {
        "status": "healthy" if chatbot else "unhealthy",
        "github_connected": bool(chatbot and chatbot.github_fetcher)
    }
    return status

@app.get("/github-projects")
def get_github_projects():
    if not chatbot or not chatbot.github_fetcher:
        return {"error": "GitHub integration not available", "projects": []}
    return {"projects": chatbot.github_fetcher.get_github_projects()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")