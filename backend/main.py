import os
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

# Import parser and analyzer modules
from chat_parser import parse_whatsapp_chat
from analyzer import analyze_chat

app = FastAPI(
    title="TeamLens API",
    description="Backend API for parsing and analyzing WhatsApp group chat contributions.",
    version="1.0.0"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Returns API health status.
    """
    return {"status": "ok"}

@app.post("/upload", tags=["Upload"])
async def upload_chat(file: UploadFile = File(...)):
    """
    Accepts a .txt WhatsApp chat export and returns parsed JSON.
    """
    if not file.filename.endswith(".txt"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Please upload a plain text (.txt) file."
        )
    
    try:
        content_bytes = await file.read()
        # Decode contents to UTF-8
        try:
            chat_text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            # Fallback to utf-8-sig or latin-1 if regular utf-8 fails
            chat_text = content_bytes.decode("utf-8-sig", errors="ignore")
            
        parsed_data = parse_whatsapp_chat(chat_text)
        return parsed_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while parsing the file: {str(e)}"
        )

@app.post("/analyze", tags=["Analyze"])
async def analyze_chat_data(parsed_data: List[Dict[str, Any]]):
    """
    Accepts parsed WhatsApp chat JSON and returns overall contribution analysis and narrative report.
    """
    if not parsed_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The parsed chat data is empty or invalid."
        )
        
    # Verify Groq API Key is present before initiating call
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GROQ_API_KEY is not configured on the backend server. Please create a .env file containing GROQ_API_KEY=your_key in the backend folder."
        )
        
    try:
        analysis_result = analyze_chat(parsed_data)
        return analysis_result
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during AI analysis: {str(e)}"
        )
