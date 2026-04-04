import os
import firebase_admin
from firebase_admin import firestore, credentials
from modules.vector_db_manager import db_manager
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Initialize Firebase with fallback
db = None
try:
    if not firebase_admin._apps:
        # Assuming the service account path is in env or a default location
        service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "service_account.json")
        if os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
        else:
            print("\n" + "!" * 50)
            print("WARNING: service_account.json not found in construction-ai-service/")
            print("RAG will run in MOCK MODE with sample data.")
            print("To use real project data, download your Firebase Admin SDK key")
            print("from Firebase Console -> Project Settings -> Service Accounts")
            print("and save it as 'service_account.json' in this folder.")
            print("!" * 50 + "\n")
except Exception as e:
    print(f"CRITICAL: Firebase initialization failed: {e}. Falling back to MOCK MODE.")

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
else:
    model = None
    print("WARNING: GEMINI_API_KEY not found in .env. AI will return raw context.")

PROMPT_TEMPLATE = """You are a construction project analyst assistant.
Answer the engineer's question using ONLY the project data provided below.
Be concise. Cite specific numbers from the data. Do not give generic advice.
If the data does not contain enough information to answer, say so clearly.

PROJECT DATA:
{context}

ENGINEER QUESTION: {question}

ANSWER:"""

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
        # 2. Fetch Last 30 Logs
        logs = db.collection("projects").document(project_id).collection("resourceLogs").order_by("logDate", direction=firestore.Query.DESCENDING).limit(30).get()
        # 3. Fetch Last 5 Deviations
        deviations = db.collection("projects").document(project_id).collection("deviations").order_by("generatedAt", direction=firestore.Query.DESCENDING).limit(5).get()

        chunks = []
        
        # Serialize Estimate
        if estimates:
            est_data = estimates[0].to_dict()
            chunks.append(f"Project Estimate (Current): {est_data.get('estimatedMaterials', {})} generated on {est_data.get('generatedAt')}. Cost: {est_data.get('estimatedCost')}")

        # Serialize Logs
        for log in logs:
            l = log.to_dict()
            chunks.append(f"On {l.get('logDate')}, {l.get('loggedBy')} logged: {l.get('materials')}. Equipment: {l.get('equipment')}. Notes: {l.get('notes')}")

        # Serialize Deviations
        for dev in deviations:
            d = dev.to_dict()
            chunks.append(f"Deviation Report: overallSeverity: {d.get('overallSeverity')}, breakdown: {d.get('deviations')}, Overrun Probability: {d.get('mlOverrunProbability')}")

        if chunks:
            self._save_to_vector_db(project_id, chunks)
        return len(chunks)

    def _save_to_vector_db(self, project_id: str, chunks: list):
        # Collection named project_{project_id}
        self.db_manager.client.get_or_create_collection(f"project_{project_id}")
        self.db_manager.add_documents(
            documents=chunks,
            metadatas=[{"project_id": project_id}] * len(chunks),
            ids=[f"{project_id}_{i}_{os.urandom(4).hex()}" for i in range(len(chunks))]
        )

    def get_answer(self, project_id: str, question: str):
        try:
            # Query the specific project collection
            collection = self.db_manager.client.get_collection(f"project_{project_id}")
            results = collection.query(query_texts=[question], n_results=5)
            context = "\n".join(results['documents'][0])
        except Exception:
            # If collection doesn't exist yet, return helpful prompt
            context = "No project data indexed yet for project: " + project_id
        
        prompt = PROMPT_TEMPLATE.format(context=context, question=question)

        # Call Gemini if available
        if model and "No project data indexed yet" not in context:
            try:
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                return f"[AI Generation Error]: {e}\n\nFalling back to raw context:\n{prompt}"
        
        return prompt

rag_engine = RAGEngine()
