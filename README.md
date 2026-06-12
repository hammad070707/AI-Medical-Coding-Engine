🏥 MediCode AI: Autonomous RCM & Medical Coding Engine

MediCode AI is an Enterprise-Grade Autonomous Medical Coding and Audit Engine. It uses Multi-Agent AI (GPT-4o) and Retrieval-Augmented Generation (RAG) to transform raw clinical notes into compliant ICD-10 and CPT codes with a self-correction loop.

🚀 Key Features

Multi-Modal Input: Processes data from Digital PDFs, Scanned Images (OCR), and Raw Text.
RAG-Powered Lookup: High-speed retrieval from official ICD-10 and CPT manuals using FAISS Vector DB.
Multi-Agent Collaborative Workflow:
Coder Agent: Assigns specific codes based on clinical evidence.
Auditor Agent: Performs a 35-year expert-level critique based on NCCI/CMS guidelines.
CDI Optimizer: Automatically suggests physician addendums to bridge documentation gaps.
Revenue Integrity Suite:
E&M Calculator: Assigns correct office visit levels based on MDM complexity.
Modifier Engine: Deterministic logic for -25, -59, -RT, -LT, and -50 modifiers.
Static Validator: Hard-coded checks for Gender, Age, and Place of Service (POS).

🛠️ Tech Stack

AI Brain: OpenAI GPT-4o & GPT-4o-mini
Vector Database: FAISS
Backend Framework: Python 3.11+
Frontend Dashboard: Streamlit
OCR/NLP: Tesseract OCR, PyMuPDF (fitz), Pydantic v2
Logging: Loguru

📁 Project Structure

code
Text
coding_service/
├── core/               # RAG, Validator, Modifiers, E&M, CDI Logic
├── agents/             # Coder & Auditor AI Agents
├── data/               # Medical Manuals (CSV) & Vector DB
├── app_dashboard.py    # SaaS Web Interface
└── main.py             # Orchestrator (The Final Pipeline)

⚙️ Quick Start
Install Tesseract OCR on your local machine.
Setup Virtual Environment:
code
uv venv
source .venv/bin/activate

Install Dependencies:
code
pip install -r requirements.txt
Environment Variables:
Create a .env file and add your OPENAI_API_KEY.
Initialize Database:
Place your ICD-10 and CPT CSV files in data/ and run the indexing script.

Launch Dashboard:
code
streamlit run app_dashboard.py

⚖️ Disclaimer

This system is intended for administrative assistance and educational purposes. All medical coding decisions should be verified by a Certified Professional Coder (CPC) to ensure full compliance with healthcare regulations.
