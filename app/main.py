import os
import socket
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

from app.rag import RAGStore
from app.llm import SynthesisEngine

load_dotenv()

app = FastAPI(
    title="BiztelAI Shop Floor Copilot",
    description="Intelligent SOP & Maintenance Copilot for Manufacturing Supervisors",
    version="1.0.0"
)

# Static and Templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Initialize RAG Store & LLM Engine
rag_store = RAGStore(data_dir="data")
rag_store.load_and_index()
llm_engine = SynthesisEngine()

def get_local_ip():
    """Finds the local network IP for Wi-Fi access."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

class QueryRequest(BaseModel):
    question: str
    provider: Optional[str] = "auto"

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(content=b"", media_type="image/x-icon")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    local_ip = get_local_ip()
    docs = [
        {
            "doc_id": m.doc_id,
            "filename": m.filename,
            "title": m.title,
            "revision": m.revision,
            "effective_date": m.effective_date,
            "is_active": m.is_active,
            "superseded_by": m.superseded_by,
            "pages": m.page_count
        }
        for m in rag_store.documents.values()
    ]
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "documents": docs,
            "local_ip": local_ip,
            "port": int(os.getenv("PORT", 8505))
        }
    )

@app.post("/api/query")
async def api_query(req: QueryRequest):
    if not req.question or not req.question.strip():
        return JSONResponse(status_code=400, content={"error": "Question cannot be empty."})

    results, found = rag_store.search(req.question.strip(), top_k=5)
    response_data = llm_engine.generate_answer(
        query=req.question.strip(),
        search_results=results,
        found=found,
        requested_provider=req.provider or "auto"
    )
    return JSONResponse(content=response_data)

@app.get("/api/documents")
async def api_documents():
    docs = [
        {
            "doc_id": m.doc_id,
            "filename": m.filename,
            "title": m.title,
            "revision": m.revision,
            "effective_date": m.effective_date,
            "is_active": m.is_active,
            "superseded_by": m.superseded_by,
            "pages": m.page_count
        }
        for m in rag_store.documents.values()
    ]
    return {"documents": docs, "total_chunks": len(rag_store.chunks)}

@app.get("/api/sample-questions")
async def api_sample_questions():
    return {
        "sample_questions": [
            {
                "id": 1,
                "category": "Assignment Samples",
                "question": "What is the recommended coolant concentration for the TX-200 CNC turning centre?"
            },
            {
                "id": 2,
                "category": "Assignment Samples",
                "question": "The machine is showing alarm AL-104. What does it mean and what should the operator do?"
            },
            {
                "id": 3,
                "category": "Assignment Samples",
                "question": "Who is allowed to remove a lockout lock from a machine?"
            },
            {
                "id": 4,
                "category": "Assignment Samples",
                "question": "What is the outer diameter tolerance for the BH-220 bearing housing?"
            },
            {
                "id": 5,
                "category": "Assignment Samples",
                "question": "How often should spindle runout be checked, and who does it?"
            },
            {
                "id": 6,
                "category": "Plant Operations & Revision Check",
                "question": "Where should rejected incoming material be moved, and who keeps the key?"
            },
            {
                "id": 7,
                "category": "Plant Operations & Revision Check",
                "question": "What torque and tightening pattern should be used when re-mounting the chuck on the TX-200 CNC?"
            },
            {
                "id": 8,
                "category": "Plant Operations & Revision Check",
                "question": "If a lot of 200 bought-out components arrives at receiving, how many samples must be inspected, and when is the lot rejected?"
            },
            {
                "id": 9,
                "category": "Plant Operations & Revision Check",
                "question": "What steps must be followed if an operator leaves the plant with their lockout lock still attached?"
            },
            {
                "id": 10,
                "category": "Negative Test (Out of Scope)",
                "question": "What is the recommended feed rate and spindle speed for cutting aluminium on the TX-200?"
            }
        ]
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "indexed_documents": len(rag_store.documents),
        "indexed_chunks": len(rag_store.chunks),
        "local_ip": get_local_ip()
    }

