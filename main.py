import os
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
YOUR_HF_MODEL_ID = "shwetgaur/SG_OG_name_generator"
# NEW, CORRECTED URL
HF_API_URL = f"https://api-inference.huggingface.co/models/{YOUR_HF_MODEL_ID}"
DOMAINR_API_URL = "https://domainr.p.rapidapi.com/v2/status"

app = FastAPI(title="BizBrand.ai API")

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

class NameRequest(BaseModel):
    description: str


@app.get("/")
def read_root():
    return {"status": "BizBrand.ai API is running."}


@app.post("/generate-name")
async def generate_name(request: NameRequest):
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
        response.raise_for_status()
        generated_data = response.json()

        if "error" in generated_data:
            # Model might still be loading
            if "is currently loading" in generated_data["error"]:
                return JSONResponse(
                    status_code=503,
                    content={"error": "Model is loading, please try again in a few seconds."}
                )
            return JSONResponse(
                status_code=500,
                content={"error": generated_data["error"]}
            )

        generated_names = [item["generated_text"] for item in generated_data]
        return {"names": generated_names}

    except requests.exceptions.RequestException as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/check-domain")
async def check_domain(domain: str):
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
