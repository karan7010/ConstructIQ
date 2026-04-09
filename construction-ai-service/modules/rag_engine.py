import os
import json
import firebase_admin
from firebase_admin import firestore, credentials
from modules.vector_db_manager import db_manager
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ── Firebase Admin SDK Initialization ──────────────────────────────────
db = None
try:
    if not firebase_admin._apps:
        # Try environment variable first (for Railway deployment)
        firebase_credentials_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
        if firebase_credentials_json:
            cred_dict = json.loads(firebase_credentials_json)
            cred = credentials.Certificate(cred_dict)
        else:
            # Fall back to local file for development
            service_account_path = os.path.join(
                os.path.dirname(__file__), '..', 'service_account.json'
            )
            if not os.path.exists(service_account_path):
                raise FileNotFoundError(
                    "service_account.json not found and FIREBASE_CREDENTIALS_JSON "
                    "env var not set. Cannot connect to Firestore."
                )
            cred = credentials.Certificate(service_account_path)

        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase Admin SDK initialized successfully.")
except FileNotFoundError as e:
    print(f"\n{'!' * 50}")
    print(f"WARNING: {e}")
    print("RAG will run in MOCK MODE with sample data.")
    print("To use real project data, download your Firebase Admin SDK key")
    print("from Firebase Console -> Project Settings -> Service Accounts")
    print("and save it as 'service_account.json' in this folder.")
    print(f"{'!' * 50}\n")
except Exception as e:
    print(f"CRITICAL: Firebase initialization failed: {e}. Falling back to MOCK MODE.")

# ── NVIDIA NIM Client Initialization (OpenAI-compatible) ───────────────
_nvidia_client = OpenAI(
    base_url=os.getenv('NVIDIA_BASE_URL', 'https://integrate.api.nvidia.com/v1'),
    api_key=os.getenv('NVIDIA_API_KEY'),
)
_nvidia_model = os.getenv('NVIDIA_MODEL', 'meta/llama-3.1-8b-instruct')

if os.getenv('NVIDIA_API_KEY'):
    print(f"NVIDIA NIM client configured (model: {_nvidia_model}).")
else:
    print("WARNING: NVIDIA_API_KEY not found in .env. AI will return raw context.")

# ── Prompt Template ────────────────────────────────────────────────────
PROMPT_TEMPLATE = """You are a construction project analyst assistant.
Answer the engineer's question using ONLY the project data provided below.
Be concise. Cite specific numbers from the data. Do not give generic advice.
If the data does not contain enough information to answer, say so clearly.

PROJECT DATA:
{context}

ENGINEER QUESTION: {question}

ANSWER:"""


def _call_llm(context: str, question: str) -> str:
    """Call NVIDIA NIM LLM with RAG context and user question."""
    
    system_prompt = (
        "You are a construction project analyst assistant for ConstructIQ. "
        "Answer the engineer's question using ONLY the project data provided below. "
        "Be concise and specific. Cite actual numbers from the data. "
        "Do not give generic construction advice. "
        "If the provided data does not contain enough information to answer, "
        "say so clearly instead of guessing."
    )
    
    user_message = f"""PROJECT DATA:
{context}

ENGINEER QUESTION: {question}

ANSWER:"""

    try:
        completion = _nvidia_client.chat.completions.create(
            model=_nvidia_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,      # Low temperature for factual RAG responses
            max_tokens=512,       # Enough for a detailed answer, not wasteful
            top_p=0.9,
        )
        return completion.choices[0].message.content.strip()
    
    except Exception as e:
        # Graceful fallback — never crash the API endpoint
        print(f"NVIDIA NIM LLM error: {e}")
        return (
            f"AI assistant is temporarily unavailable. "
            f"Here is the raw context for your question:\n\n"
            f"{context[:500]}..."
        )


class RAGEngine:
    def __init__(self):
        self.db_manager = db_manager

    def index_project_data(self, project_id: str):
        """Indexes estimates and last 30 logs for a specific project."""
        if db is None:
            # RETURN MOCK DATA FOR DEMO
            mock_chunks = [
                f"Project Estimate (Current): {{'bricks': 5000, 'cement': 200}} Status: published",
                "On 2026-03-20, Site Engineer logged: {'bricks': 500, 'cement': 20}. Notes: Standard brickwork starting.",
                "On 2026-03-21, Site Engineer logged: {'bricks': 600, 'cement': 25}. Notes: Progress steady.",
                "Deviation Report: overallSeverity: critical, breakdown: {'bricks': 0.15}"
            ]
            self._save_to_vector_db(project_id, mock_chunks)
            return len(mock_chunks)

        # 1. Fetch Latest Estimate
        estimates = db.collection("projects").document(project_id).collection("estimates").order_by("generatedAt", direction=firestore.Query.DESCENDING).limit(1).get()
        # 2. Fetch Last 30 Logs (field is 'date', not 'logDate')
        logs = db.collection("projects").document(project_id).collection("resourceLogs").order_by("date", direction=firestore.Query.DESCENDING).limit(30).get()
        # 3. Fetch Last 5 Deviations
        deviations = db.collection("projects").document(project_id).collection("deviations").order_by("createdAt", direction=firestore.Query.DESCENDING).limit(5).get()

        chunks = []

        # Serialize Estimate (NO cost field — deliberate design decision)
        if estimates:
            est_data = estimates[0].to_dict()
            chunks.append(f"Project Estimate (Current): {est_data.get('estimatedMaterials', {})} generated on {est_data.get('generatedAt')}. Labour: {est_data.get('labour', {})}. Total Labour Days: {est_data.get('totalLabourDays')}")

        # Serialize Logs (field names: 'date', 'materialUsage')
        for log in logs:
            l = log.to_dict()
            chunks.append(f"On {l.get('date')}, {l.get('loggedBy')} logged: {l.get('materialUsage', l.get('materials', {}))}. Equipment: {l.get('equipment')}. Notes: {l.get('notes')}")

        # Serialize Deviations (field is 'breakdown', not 'deviations')
        for dev in deviations:
            d = dev.to_dict()
            chunks.append(f"Deviation Report: overallSeverity: {d.get('overallSeverity')}, breakdown: {d.get('breakdown')}, Overrun Probability: {d.get('mlOverrunProbability')}")

        if chunks:
            self._save_to_vector_db(project_id, chunks)
        return len(chunks)

    def _save_to_vector_db(self, project_id: str, chunks: list):
        collection_name = f"project_{project_id}"
        # Delete existing collection for clean re-index
        try:
            self.db_manager.client.delete_collection(collection_name)
        except Exception:
            pass
        # Create fresh collection with embedding function
        collection = self.db_manager.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.db_manager.embedding_fn
        )
        collection.add(
            documents=chunks,
            metadatas=[{"project_id": project_id}] * len(chunks),
            ids=[f"{project_id}_{i}_{os.urandom(4).hex()}" for i in range(len(chunks))]
        )

    def get_answer(self, project_id: str, question: str):
        try:
            # Query the specific project collection with embedding function
            collection = self.db_manager.client.get_or_create_collection(
                name=f"project_{project_id}",
                embedding_function=self.db_manager.embedding_fn
            )
            if collection.count() == 0:
                raise ValueError("Empty collection")
            results = collection.query(query_texts=[question], n_results=10)
            context = "\n".join(results['documents'][0])
        except Exception:
            # If collection doesn't exist yet, return helpful prompt
            context = "No project data indexed yet for project: " + project_id

        # Call NVIDIA NIM if API key is available
        if os.getenv('NVIDIA_API_KEY'):
            return _call_llm(context=context, question=question)

        # Fallback to a simple message if no AI key configured
        return "AI assistant is not configured. Please set NVIDIA_API_KEY in the server .env file."

rag_engine = RAGEngine()
