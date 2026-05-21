AI Email Agent Backend

Overview

This project is a backend system that processes emails using a structured AI pipeline. It ingests emails, classifies them, retrieves relevant knowledge, decides an action, generates a response, and stores everything in a database.

The system is built using FastAPI and SQLite, with a modular but simple architecture.

Features

Email ingestion through API  
Batch processing of dataset  
Email classification based on rules  
Lightweight RAG using keyword matching  
Agent decision making (auto reply or escalate)  
Automated response generation  
SQLite database storage  
Thread and email retrieval endpoints  

AI Components

Classification  
The system classifies emails into categories such as complaint, refund, security, or inquiry. It also assigns urgency and sentiment based on keywords.

RAG  
A simple knowledge base is used with predefined policies. The system matches keywords from the email body to retrieve relevant information.

Agent Decision  
Based on classification and retrieved knowledge, the system decides whether to automatically reply or escalate the email.

Response Generation  
Replies are generated using structured templates including greeting, understanding, solution, and closing.

System Architecture (All diagrams present in assests folder)

The client sends requests to FastAPI endpoints.  
FastAPI routes the request to the API layer.  
The API layer calls the services layer.  
The services layer handles classification, RAG, and agent logic.  
The final output is stored in SQLite and returned to the user.  

Processing Flow

Email comes in through API  
Validated using schema  
Checked for duplicates  
Classified into category and urgency  
Relevant knowledge retrieved  
Decision made by agent  
Reply generated  
Stored in database  
Response returned  

Project Structure

backend

app  
main.py contains the FastAPI application  
api contains route handlers  
models contains request and response schemas  
services contains business logic  
agent contains decision logic  
rag contains knowledge retrieval logic  
utils contains helper functions  

email-data-advanced.json is the dataset  
emails.db is the SQLite database  
requirements.txt contains dependencies  

Tech Stack

Backend FastAPI  
Server Uvicorn  
Validation Pydantic  
Database SQLite  
Language Python  

Tech Stack Justification

FastAPI  
FastAPI was chosen because it is lightweight, fast to develop with, and provides automatic API documentation through Swagger. It is well suited for building REST APIs and allows quick testing of endpoints without additional setup. For this assignment, it helps focus on logic rather than framework complexity.

SQLite  
SQLite was used as the database because it is simple, serverless, and requires no configuration. Since the dataset is small and the project does not require high scalability, SQLite is sufficient. It also makes the project easy to run locally without external dependencies.

Pydantic  
Pydantic is used for request validation and data modeling. It ensures that incoming email data follows the expected structure and reduces errors in processing. It integrates well with FastAPI and keeps the code clean and reliable.

Python  
Python was chosen because it is easy to read, quick to develop in, and has strong support for building backend systems and AI-related logic. It allows implementing classification, decision logic, and RAG in a simple and understandable way.

Rule-Based Classification  
Instead of using machine learning models, a rule-based approach was used for classification. This decision was made to keep the system lightweight, explainable, and aligned with assignment constraints. It ensures predictable outputs and avoids dependency on external APIs.

Keyword-Based RAG  
A simple keyword matching approach was used instead of a vector database or embeddings. This reduces complexity and keeps the system easy to understand and run locally. It is sufficient for demonstrating the concept of retrieval-augmented generation within the scope of the assignment.

Template-Based Response Generation  
Responses are generated using predefined templates instead of LLMs. This ensures consistency, avoids external API usage, and keeps the system deterministic. It also makes debugging and evaluation easier.

Modular Architecture  
The project is structured into API, services, agent, and RAG layers. This separation improves readability, maintainability, and scalability. Each component has a clear responsibility, making the system easier to extend in the future.

No External AI APIs  
External AI services were intentionally not used to keep the project self-contained, reproducible, and aligned with assignment constraints. This also avoids dependency on API keys and network calls.

The overall design prioritizes simplicity, clarity, and ease of execution over scalability, as the goal of the assignment is to demonstrate system design and reasoning rather than production-level infrastructure.


How to Run

Clone the repository  

git clone https://github.com/msharsh1/senai-email-agent/ 
cd backend  

Create virtual environment  

python -m venv venv  
venv Scripts activate  

Install dependencies  

pip install -r requirements.txt  

Run server  

uvicorn app.main:app --reload

Open browser  

http://127.0.0.1:8000/docs  

API Endpoints

POST /api/ingest  
Processes a single email  

GET /process-dataset  
Processes all emails from dataset  

GET /emails  
Returns all stored emails  

GET /threads/{sender}  
Returns emails filtered by sender  



How to Test the Project

Start the server using:

uvicorn app.main:app --reload

Step 1: Check if API is running  
Open the browser and go to:  
http://127.0.0.1:8000/

You should see:  
{ "message": "API is running" }

Step 2: Open API documentation  
Go to:  
http://127.0.0.1:8000/docs

This will open Swagger UI where all endpoints can be tested.

Step 3: Process dataset  
In Swagger UI, run:  
GET /process-dataset  

This will process all emails from the dataset and store them in the database.

Step 4: View stored emails  
Run:  
GET /emails  

This will return all processed emails.

Step 5: Test single email processing  
Use:  
POST /api/ingest  

Example input:

Refund Request
{
  "sender": "test@example.com",
  "subject": "Refund issue",
  "body": "I requested a refund but have not received it.",
  "timestamp": "2026-05-21T10:00:00"
}
OR
Complaint (angry tone)
{
  "sender": "angry.customer@example.com",
  "subject": "Very disappointed with service",
  "body": "This is unacceptable. My issue has not been resolved despite multiple follow-ups.",
  "timestamp": "2026-05-21T10:15:00"
}
OR
General Inquiry
{
  "sender": "user123@example.com",
  "subject": "Question about pricing",
  "body": "Can you please provide details about your pricing plans and any discounts available?",
  "timestamp": "2026-05-21T10:20:00"
}
OR
Security Concern
{
  "sender": "secure.user@example.com",
  "subject": "Suspicious activity on my account",
  "body": "I noticed a login from an unknown device. Please secure my account immediately.",
  "timestamp": "2026-05-21T10:25:00"
}
OR
Positive Feedback
{
  "sender": "happy.customer@example.com",
  "subject": "Great service",
  "body": "I just wanted to say that I am very happy with your service. Keep up the good work!",
  "timestamp": "2026-05-21T10:30:00"
}
OR 
Escalation Case (should trigger agent logic)
{
  "sender": "frustrated.user@example.com",
  "subject": "Issue still unresolved",
  "body": "I have already contacted support twice and my problem is still not fixed. I need urgent help.",
  "timestamp": "2026-05-21T10:35:00"
}

This will return a generated response along with decision and reasoning.

Step 6: View email threads  
Run:  
GET /threads/{sender}  

Replace sender with an email address to fetch related emails.

Dataset

The dataset file contains sample emails used for testing batch processing.  

Design Decisions

No external AI APIs are used  
RAG is implemented using keyword matching  
SQLite is used for simplicity  
System is designed as a single backend service  

Out of Scope

No frontend or UI  
No authentication  
No deployment setup  
No external vector database  
No external LLM integration  

Summary

This project demonstrates a complete email processing pipeline with classification, retrieval, decision making, and response generation. It focuses on clarity, simplicity, and practical system design.