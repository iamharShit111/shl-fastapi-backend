from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json

app = FastAPI()

# Allow all CORS origins for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load sample test database
with open("tests_db.json") as f:
    test_db = json.load(f)

@app.post("/recommend")
async def recommend(request: Request):
    data = await request.json()
    query = data.get("query", "").lower()

    # Very simple matching logic: return tests with any skill mentioned in query
    matches = []
    for test in test_db:
        if any(skill.lower() in query for skill in test["skills"]):
            matches.append(test)

    # Fallback: return top 3 tests if nothing matched
    if not matches:
        matches = test_db[:3]

    return {"recommendations": matches[:10]}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)