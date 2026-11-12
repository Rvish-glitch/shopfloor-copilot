import urllib.request
import json
import time

questions = [
    {
        "id": "Sample 1",
        "q": "What is the recommended coolant concentration for the TX-200 CNC turning centre?",
        "expected_facts": ["6 - 8 %", "refractometer", "MNT-MAN-CNC-02"]
    },
    {
        "id": "Sample 2",
        "q": "The machine is showing alarm AL-104. What does it mean and what should the operator do?",
        "expected_facts": ["lube", "ISO VG 68", "RESET"]
    },
    {
        "id": "Sample 3",
        "q": "Who is allowed to remove a lockout lock from a machine?",
        "expected_facts": ["only their own lock", "SAF-SOP-003"]
    },
    {
        "id": "Sample 4",
        "q": "What is the outer diameter tolerance for the BH-220 bearing housing?",
        "expected_facts": ["90.000", "+/- 0.050", "QC-SOP-014"]
    },
    {
        "id": "Sample 5",
        "q": "How often should spindle runout be checked, and who does it?",
        "expected_facts": ["Monthly", "Maintenance technician"]
    },
    {
        "id": "Custom 1",
        "q": "Where should rejected incoming material be moved, and who keeps the key?",
        "expected_facts": ["Quarantine Cage Q1", "Shift QC Supervisor"]
    },
    {
        "id": "Custom 2",
        "q": "What torque and tightening pattern should be used when re-mounting the chuck on the TX-200 CNC?",
        "expected_facts": ["110 Nm", "criss-cross"]
    },
    {
        "id": "Custom 3",
        "q": "If a lot of 200 bought-out components arrives at receiving, how many samples must be inspected, and when is the lot rejected?",
        "expected_facts": ["13", "samples"]
    },
    {
        "id": "Custom 4",
        "q": "What steps must be followed if an operator leaves the plant with their lockout lock still attached?",
        "expected_facts": ["Production Manager", "Safety Officer", "SF-12"]
    },
    {
        "id": "Custom 5 (Out of Scope)",
        "q": "What is the recommended feed rate and spindle speed for cutting aluminium on the TX-200?",
        "expected_facts": ["Not found in documents"]
    },
    {
        "id": "Extra 1",
        "q": "What is zero energy state?",
        "expected_facts": ["all energy sources are isolated", "stored energy is released"]
    },
    {
        "id": "Extra 2",
        "q": "What does alarm AL-210 mean and what should the operator do?",
        "expected_facts": ["Chuck clamp not confirmed", "Do not start cycle"]
    }
]

print(f"Running evaluation on {len(questions)} questions against http://127.0.0.1:8505/api/query...\n")

results_summary = []

for item in questions:
    q = item["q"]
    t0 = time.time()
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8505/api/query",
            data=json.dumps({"question": q}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read().decode("utf-8"))
        dt = time.time() - t0
        
        ans = data.get("answer", "")
        found = data.get("found", False)
        
        # Check expected facts
        missing = [f for f in item["expected_facts"] if f.lower() not in ans.lower()]
        status = "PASS" if not missing else f"FAIL (missing: {missing})"
        
        results_summary.append({
            "id": item["id"],
            "status": status,
            "latency": round(dt, 2),
            "answer_preview": ans[:140].replace("\n", " ")
        })
        
        print(f"[{item['id']}] ({dt:.2f}s) -> {status}")
        print(f"  Q: {q}")
        print(f"  A: {ans}")
        print("-" * 70)
    except Exception as e:
        print(f"[{item['id']}] ERROR: {e}")
        results_summary.append({"id": item["id"], "status": f"ERROR: {e}", "latency": 0, "answer_preview": ""})

print("\n=== SUMMARY EVALUATION REPORT ===")
for r in results_summary:
    print(f"{r['id']:<25} | {r['status']:<15} | {r['latency']}s | {r['answer_preview'][:60]}")

