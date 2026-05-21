from fastapi import FastAPI
from pydantic import BaseModel
import uuid
from typing import List

app = FastAPI()

# In-memory DB
emails_db = []
actions_db = []

class Email(BaseModel):
    sender: str
    subject: str
    body: str
    timestamp: str

# Fake RAG knowledge
KNOWLEDGE_BASE = {
    "refund": "Refunds are allowed within 30 days as per company policy.",
    "sla": "SLA guarantees 99.9% uptime with compensation for breaches.",
    "pricing": "Our pricing starts at $29/month."
}

# Simple classifier (FAKE AI)
def classify_email(email):
    text = email.body.lower()

    if "refund" in text:
        return {"category": "refund", "urgency": "medium", "sentiment": -0.2}
    elif "not working" in text or "issue" in text:
        return {"category": "complaint", "urgency": "high", "sentiment": -0.7}
    elif "thank" in text:
        return {"category": "positive", "urgency": "low", "sentiment": 0.8}
    else:
        return {"category": "general", "urgency": "low", "sentiment": 0}

# Simple RAG retrieval
def get_knowledge(category):
    return KNOWLEDGE_BASE.get(category, "No policy found.")

# Simple agent
def agent_decision(email, classification):
    reasoning = []

    reasoning.append(f"Detected category: {classification['category']}")
    reasoning.append(f"Urgency: {classification['urgency']}")

    if classification["urgency"] == "high":
        action = "escalate"
    else:
        action = "auto-reply"

    knowledge = get_knowledge(classification["category"])

    reply = f"""
    Thank you for your email.

    Based on our policy: {knowledge}

    We will assist you shortly.
    """

    return {
        "action": action,
        "reply": reply,
        "reasoning": reasoning
    }

@app.get("/")
def root():
    return {"message": "API is running"}

@app.post("/api/ingest")
def ingest_email(email: Email):
    email_id = str(uuid.uuid4())

    classification = classify_email(email)
    decision = agent_decision(email, classification)

    record = {
        "id": email_id,
        "email": email.dict(),
        "classification": classification,
        "decision": decision
    }

    emails_db.append(record)

    return {
        "email_id": email_id,
        "action": decision["action"],
        "reasoning": decision["reasoning"]
    }

@app.get("/emails")
def get_emails():
    return emails_db

@app.get("/threads/{sender}")
def get_thread(sender: str):
    return [e for e in emails_db if e["email"]["sender"] == sender]