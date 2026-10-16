from fastapi import FastAPI
from pydantic import BaseModel
from src.agent import run_agent

app = FastAPI()

class Question(BaseModel):
    text: str

@app.get("/")
def root():
    return {"status": "Onboarding Brain is running"}

@app.post("/ask")
def ask(q: Question):
    result = run_agent(q.text, verbose=False)
    return result