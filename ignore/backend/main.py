# backend/main.py - Successfully configured with Google OAuth and Figma-to-React generation
import sys
import os

# Load environment variables from .env file FIRST
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add the current directory to sys.path to ensure modules like 'domains' and 'mcp_tools' can be imported
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from langraph.api_endpoint import router

app = FastAPI(title="Disco Dashboard API")

# Enable CORS for the Chrome Extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your extension ID
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the dashboard generation router
app.include_router(router)

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Disco Dashboard Backend is running",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Disco Dashboard Server...")
    uvicorn.run(app, host="0.0.0.0", port=8083)
