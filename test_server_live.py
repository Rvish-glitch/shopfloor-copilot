import uvicorn
import threading
import time
import httpx
from app.main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
time.sleep(1.5)

client = httpx.Client(base_url="http://127.0.0.1:8001", timeout=10.0)

try:
    # 1. Health check
    h = client.get("/health")
    print("GET /health ->", h.status_code, h.json())

    # 2. Index HTML
    idx = client.get("/")
    print("GET / ->", idx.status_code, "HTML length:", len(idx.text))

    # 3. Documents list
    docs = client.get("/api/documents")
    print("GET /api/documents ->", docs.status_code, "Docs count:", len(docs.json()["documents"]))

    # 4. Sample Question 1 query
    q1 = {"question": "What is the recommended coolant concentration for the TX-200 CNC turning centre?"}
    ans1 = client.post("/api/query", json=q1)
    print("POST /api/query (Q1) ->", ans1.status_code, "Found:", ans1.json()["found"])
    print("Answer snippet:", ans1.json()["answer"][:100].replace("\n", " "))

    # 5. Out of scope query
    q_out = {"question": "What is the recommended feed rate and spindle speed for cutting aluminium on the TX-200?"}
    ans_out = client.post("/api/query", json=q_out)
    print("POST /api/query (Out of Scope) ->", ans_out.status_code, "Found:", ans_out.json()["found"])
    print("Answer snippet:", ans_out.json()["answer"][:100].replace("\n", " "))

    print("\nALL LIVE ENDPOINTS TESTED SUCCESSFULLY!")
except Exception as e:
    print("Error during live testing:", e)
    raise

