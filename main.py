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
YOUR_HF_MODEL_ID = "shwetgaur/SG_OG_name_generator"  # <-- CORRECTED
# NEW, CORRECTED CODE
HF_API_URL = f"https://router.huggingface.co/hf-inference/models/{YOUR_HF_MODEL_ID}"

# This is the new Domainr API endpoint
DOMAINR_API_URL = "https://domainr.p.rapidapi.com/v2/status"  # <-- REPLACEMENT


# --- FastAPI App Initialization ---
app = FastAPI(title="BizBrand.ai API")

# --- Pydantic Models (for request data validation) ---
class NameRequest(BaseModel):
    description: str

# --- CORS Middleware ---
# IMPORTANT: You MUST update this list with your real Vercel URL
origins = [
    "http://localhost:3000",  # For local Next.js development
    "https://bizbrand-frontend-n3ysxowo4-shwetgaurs-projects.vercel.app" # <-- PUT YOUR DEPLOYED FRONTEND URL HERE
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
        
        generated_data = response.json()
        
        # Handle cases where the model might not be loaded yet
        if "error" in generated_data:
             # Model is likely loading, tell the user to try again
            if "is currently loading" in generated_data["error"]:
                return {"error": "Model is loading, please try again in a few seconds."}, 503
            return {"error": generated_data["error"]}, 500

        # The HF API returns a list of dicts, e.g., [{"generated_text": "Name 1"}]
        generated_names = [item['generated_text'] for item in generated_data]
        return {"names": generated_names}
        
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500


# --- THIS IS THE NEW, CORRECTED DOMAIN CHECK FUNCTION ---
@app.get("/check-domain")
async def check_domain(domain: str):
    """
    Checks the availability of a single domain name using the RapidAPI (Domainr) API.
    """
    
    # We check for the .com extension by default.
    domain_to_check = f"{domain}.com"
    
    querystring = {"domain": domain_to_check}
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "domainr.p.rapidapi.com"
    }

    try:
        response = requests.get(DOMAINR_API_URL, headers=headers, params=querystring)
        response.raise_for_status()
        
        data = response.json()
        
        # Domainr returns a list of 'status' objects. We find the one for our exact domain.
        status_info = data.get("status", [])[0]
        domain_status = status_info.get("status", "unknown") # e.g., "inactive", "active"
        
        # "inactive" means available
        is_available = domain_status == "inactive"
        
        return {"domain": domain_to_check, "available": is_available}

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 500
    except IndexError:
        # This happens if Domainr returns an empty status list
        return {"error": "Could not get status for domain."}, 500