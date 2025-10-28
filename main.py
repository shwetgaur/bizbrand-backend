import os
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")

# This is your fine-tuned model ID from Hugging Face
# (e.g., "PrikshitGaur/my-bart-name-generator")
YOUR_HF_MODEL_ID = "YOUR_HF_MODEL_ID_GOES_HERE" 
HF_API_URL = f"https://api-inference.huggingface.co/models/{YOUR_HF_MODEL_ID}"

GODADDY_API_URL = "https://api.godaddy.com/v1/domains/available"

# --- FastAPI App Initialization ---
app = FastAPI(title="BizBrand.ai API")

# --- Pydantic Models (for request data validation) ---
class NameRequest(BaseModel):
    description: str

# --- CORS Middleware ---
# This is CRITICAL to allow your frontend (on a different domain)
# to make requests to this backend.
origins = [
    "http://localhost:3000",  # For local Next.js development
    "https://your-frontend-domain.com" # Your deployed Vercel URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)


# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "BizBrand.ai API is running."}


@app.post("/generate-name")
async def generate_name(request: NameRequest):
    """
    Receives a business description and returns name suggestions
    from your fine-tuned Hugging Face model.
    """
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    
    # We use beam search as you did in your project
    payload = {
        "inputs": request.description,
        "parameters": {
            "num_return_sequences": 5,
            "num_beams": 10
        }
    }
    
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
        
        # The HF API returns a list of dicts, e.g., [{"generated_text": "Name 1"}]
        generated_names = [item['generated_text'] for item in response.json()]
        return {"names": generated_names}
        
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500


@app.get("/check-domain")
async def check_domain(domain: str):
    """
    Checks the availability of a single domain name using the GoDaddy API.
    """
    headers = {
        "Authorization": f"sso-key {GODADDY_KEY}:{GODADDY_SECRET}"
    }
    
    try:
        # We check for the .com extension by default.
        domain_to_check = f"{domain}.com"
        
        url = f"{GODADDY_API_URL}?domain={domain_to_check}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        # 'available' is a boolean in the GoDaddy response
        return {"domain": data.get("domain"), "available": data.get("available")}

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500