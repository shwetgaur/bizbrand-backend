import os
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from transformers import pipeline

# Load environment variables
load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
YOUR_HF_MODEL_ID = "shwetgaur/SG_OG_name_generator"
DOMAINR_API_URL = "https://domainr.p.rapidapi.com/v2/status"

# Initialize FastAPI
app = FastAPI(title="BizBrand.ai API")

# Allow frontend access
origins = [
    "http://localhost:3000",
    "https://bizbrand-frontend.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the Hugging Face model locally (only once)
print("🔄 Loading Hugging Face model... please wait.")
generator = pipeline("text2text-generation", model=YOUR_HF_MODEL_ID)
print("✅ Model loaded successfully!")

# Request model
class NameRequest(BaseModel):
    description: str


@app.get("/")
def read_root():
    return {"status": "BizBrand.ai API is running."}


@app.post("/generate-name")
async def generate_name(request: NameRequest):
    """
    Generate 4 creative business names based on description using your fine-tuned T5 model.
    """
    try:
        prompt = f"Generate 4 creative business names for: {request.description}"

        # Generate names using your fine-tuned model
        results = generator(
            prompt,
            max_new_tokens=40,
            num_return_sequences=4,  # must be ≤ num_beams
            num_beams=4,
            do_sample=True,
            temperature=0.8
        )

        # Extract names and remove duplicates / formatting
        generated_names = list({res["generated_text"].strip() for res in results})
        generated_names = [name.replace("\n", " ").strip() for name in generated_names]

        return {"names": generated_names}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/check-domain")
async def check_domain(domain: str):
    """
    Check if a .com domain is available using Domainr API.
    """
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

        status_info = data.get("status", [])[0]
        domain_status = status_info.get("status", "unknown")
        is_available = domain_status == "inactive"

        return {"domain": domain_to_check, "available": is_available}

    except requests.exceptions.RequestException as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    except IndexError:
        return JSONResponse(status_code=500, content={"error": "Could not get status for domain."})
