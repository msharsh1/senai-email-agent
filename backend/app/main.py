from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path
import json
import sqlite3
from typing import Any

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "emails.db"
DATASET_PATH = BASE_DIR / "email-data-advanced.json"

KNOWLEDGE_BASE: list[dict[str, Any]] = [
    {
        "text": "Refunds are available within 14 days of purchase. After 14 days, account credits may be offered instead. Escalate churn-risk cases to retention.",
        "tags": ["refund", "money back", "cancel subscription", "unhappy", "credit"],
    },
    {
        "text": "Our uptime SLA is 99.9%. P0 incidents require immediate response. SLA credits apply for qualifying downtime. RCA reports for P0 must be delivered within 24 hours.",
        "tags": ["sla", "uptime", "downtime", "p0", "incident", "outage", "production down", "breach"],
    },
    {
        "text": "Standard plan starts at $29/month. Enterprise and non-profit pricing is available; registered 501(c)(3) organizations may qualify for a 30% discount on Standard.",
        "tags": ["pricing", "price", "discount", "non-profit", "nonprofit", "501", "enterprise plan", "billing"],
    },
    {
        "text": "API v2 requires a separate scope from v1. Rate limits vary by tier. Use valid API keys and correct headers for POST /v2/events and related endpoints.",
        "tags": ["api", "endpoint", "403", "integration", "webhook", "api key", "/v2/", "permission scope"],
    },
    {
        "text": "We support GDPR data portability requests and HIPAA BAA for enterprise customers. SOC 2 Type II certified. Route formal compliance requests to the legal team.",
        "tags": ["gdpr", "hipaa", "compliance", "data portability", "baa", "soc 2", "legal obligation"],
    },
    {
        "text": "Escalate immediately for: legal threats, security incidents, ransomware, VIP churn, and public review threats. Do not send generic auto-replies on critical issues.",
        "tags": ["legal", "lawsuit", "cease and desist", "ransomware", "security", "escalation", "review", "trustpilot", "churn"],
    },
    {
        "text": "Standard support responds within one business day. Technical issues are triaged by severity. Follow-up emails from the same sender should reference prior context.",
        "tags": ["support", "help", "issue", "bug", "not working", "follow up", "checking in"],
    },
]


class Email(BaseModel):
    message_id: str | None = None
    thread_id: str | None = None
    sender: str
    subject: str
    body: str
    timestamp: str


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS emails (
                id TEXT PRIMARY KEY,
                sender TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                thread_id TEXT,
                classification TEXT NOT NULL,
                action TEXT NOT NULL,
                reply TEXT NOT NULL,
                reasoning TEXT NOT NULL
            )
            """
        )
        conn.commit()


def email_exists(message_id: str) -> bool:
    with get_db() as conn:
        row = conn.execute("SELECT 1 FROM emails WHERE id = ?", (message_id,)).fetchone()
    return row is not None


def save_email_record(
    message_id: str,
    email: Email,
    classification: dict,
    action: str,
    reply: str,
    reasoning: list[str],
) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO emails (
                id, sender, subject, body, timestamp, thread_id,
                classification, action, reply, reasoning
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                email.sender,
                email.subject,
                email.body,
                email.timestamp,
                email.thread_id,
                json.dumps(classification),
                action,
                reply,
                json.dumps(reasoning),
            ),
        )
        conn.commit()


def row_to_record(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "email": {
            "message_id": row["id"],
            "thread_id": row["thread_id"],
            "sender": row["sender"],
            "subject": row["subject"],
            "body": row["body"],
            "timestamp": row["timestamp"],
        },
        "classification": json.loads(row["classification"]),
        "decision": {
            "action": row["action"],
            "reply": row["reply"],
            "reasoning": json.loads(row["reasoning"]),
        },
    }


def resolve_message_id(email: Email) -> str:
    if email.message_id:
        return email.message_id
    seed = f"{email.sender}|{email.subject}|{email.timestamp}|{email.body[:120]}"
    return f"ingest_{abs(hash(seed))}"


def classify_email(email: Email) -> dict:
    text = f"{email.subject} {email.body}".lower()

    if any(k in text for k in ("ransomware", "data breach", "suspicious login", "unauthorized access")):
        category, urgency, sentiment = "security", "high", -0.9
    elif any(k in text for k in ("gdpr", "hipaa", "compliance", "data portability")):
        category, urgency, sentiment = "compliance", "high", -0.3
    elif any(k in text for k in ("refund", "money back", "cancel subscription")):
        category, urgency, sentiment = "refund", "medium", -0.5
    elif any(k in text for k in ("sla", "downtime", "p0", "outage", "production", "not responding")):
        category, urgency, sentiment = "sla", "high", -0.8
    elif any(k in text for k in ("pricing", "discount", "non-profit", "nonprofit", "501", "enterprise plan")):
        category, urgency, sentiment = "pricing", "low", 0.2
    elif any(k in text for k in ("api", "endpoint", "403", "webhook", "/v2/")):
        category, urgency, sentiment = "api", "medium", -0.2
    elif any(k in text for k in ("seo", "click here", "limited offer", "sir/madam", "nigerian")):
        category, urgency, sentiment = "spam", "low", -0.1
    elif any(k in text for k in ("legal", "lawsuit", "cease and desist", "attorney")):
        category, urgency, sentiment = "legal", "high", -0.7
    elif any(k in text for k in ("not working", "issue", "bug", "unhappy", "slow")):
        category, urgency, sentiment = "complaint", "high", -0.7
    elif any(k in text for k in ("thank", "appreciate", "great job", "love the")):
        category, urgency, sentiment = "positive", "low", 0.8
    else:
        category, urgency, sentiment = "general", "low", 0.0

    if any(k in text for k in ("urgent", "p0", "immediately", "asap")):
        urgency = "high"

    return {"category": category, "urgency": urgency, "sentiment": sentiment}


def retrieve_knowledge(body: str, limit: int = 3) -> list[str]:
    text = body.lower()
    scored: list[tuple[int, str]] = []

    for entry in KNOWLEDGE_BASE:
        score = sum(1 for tag in entry["tags"] if tag in text)
        if score > 0:
            scored.append((score, entry["text"]))

    scored.sort(key=lambda item: item[0], reverse=True)
    if not scored:
        return ["Our team will review your message and follow up with the most relevant policy guidance."]

    return [text for _, text in scored[:limit]]


def sender_display_name(sender: str) -> str:
    local = sender.split("@")[0].replace(".", " ").replace("_", " ")
    return local.title()


def generate_reply(email: Email, classification: dict, knowledge_chunks: list[str]) -> str:
    name = sender_display_name(email.sender)
    category = classification["category"]
    policy = " ".join(knowledge_chunks)

    understanding = {
        "refund": "I understand you are dissatisfied and are asking about a refund or billing adjustment.",
        "sla": "I understand you are reporting a service disruption and are concerned about impact and SLA obligations.",
        "pricing": "I understand you have questions about pricing, plans, or available discounts.",
        "api": "I understand you are facing a technical integration issue with our API.",
        "compliance": "I understand this relates to compliance, data protection, or contractual requirements.",
        "complaint": "I understand you are experiencing a product or service issue that needs attention.",
        "security": "I understand this may involve a security-related concern that requires urgent handling.",
        "legal": "I understand this message may involve a legal or contractual matter.",
        "spam": "We have received your message.",
        "positive": "Thank you for sharing your positive feedback.",
        "general": "Thank you for reaching out to us.",
    }.get(category, "Thank you for contacting us.")

    reassurance = (
        "Your message has been prioritized for review by the appropriate team, and we will follow up with clear next steps."
        if classification["urgency"] == "high"
        else "We are here to help and will make sure you receive a thoughtful response shortly."
    )

    return (
        f"Dear {name},\n\n"
        f"{understanding}\n\n"
        f"Regarding your email about \"{email.subject}\", here is the relevant policy information: {policy}\n\n"
        f"{reassurance}\n\n"
        f"Kind regards,\nCustomer Support Team"
    )


def agent_decision(email: Email, classification: dict, knowledge_chunks: list[str]) -> dict:
    reasoning = [
        f"Detected category: {classification['category']}",
        f"Urgency: {classification['urgency']}",
        f"Sentiment score: {classification['sentiment']}",
        f"Retrieved {len(knowledge_chunks)} knowledge snippet(s) from keyword match.",
    ]

    if classification["category"] in {"spam", "security", "legal"}:
        action = "escalate"
        reasoning.append("Category requires human or specialized team handling.")
    elif classification["urgency"] == "high":
        action = "escalate"
        reasoning.append("High urgency detected; routing for human review.")
    else:
        action = "auto-reply"
        reasoning.append("Standard auto-reply is appropriate for this message.")

    reply = generate_reply(email, classification, knowledge_chunks)

    return {"action": action, "reply": reply, "reasoning": reasoning}


def process_email(email: Email) -> tuple[bool, dict]:
    message_id = resolve_message_id(email)

    if email_exists(message_id):
        return False, {"email_id": message_id, "skipped": True}

    classification = classify_email(email)
    knowledge_chunks = retrieve_knowledge(f"{email.subject} {email.body}")
    decision = agent_decision(email, classification, knowledge_chunks)

    save_email_record(
        message_id,
        email,
        classification,
        decision["action"],
        decision["reply"],
        decision["reasoning"],
    )

    return True, {
        "email_id": message_id,
        "action": decision["action"],
        "reasoning": decision["reasoning"],
        "skipped": False,
    }


def load_dataset() -> list[dict]:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")
    with DATASET_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def process_dataset_batch() -> dict[str, int]:
    processed = 0
    skipped = 0

    for item in load_dataset():
        email = Email(
            message_id=item["message_id"],
            thread_id=item.get("thread_id"),
            sender=item["sender"],
            subject=item["subject"],
            body=item["body"],
            timestamp=item["timestamp"],
        )
        was_processed, _ = process_email(email)
        if was_processed:
            processed += 1
        else:
            skipped += 1

    return {"processed": processed, "skipped": skipped}


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def root() -> dict:
    return {"message": "API is running"}


@app.post("/api/ingest")
def ingest_email(email: Email) -> dict:
    was_processed, result = process_email(email)
    if not was_processed:
        with get_db() as conn:
            row = conn.execute("SELECT * FROM emails WHERE id = ?", (result["email_id"],)).fetchone()
        if row:
            record = row_to_record(row)
            return {
                "email_id": result["email_id"],
                "action": record["decision"]["action"],
                "reasoning": record["decision"]["reasoning"],
                "skipped": True,
            }
        raise HTTPException(status_code=409, detail="Duplicate message_id")
    return result


@app.get("/emails")
def get_emails() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM emails ORDER BY timestamp ASC").fetchall()
    return [row_to_record(row) for row in rows]


@app.get("/threads/{sender}")
def get_thread(sender: str) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM emails WHERE sender = ? ORDER BY timestamp ASC",
            (sender,),
        ).fetchall()
    return [row_to_record(row) for row in rows]


@app.get("/process-dataset")
def process_dataset() -> dict[str, int]:
    return process_dataset_batch()


init_db()
