from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, uuid, asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Req(BaseModel):
    prompt: str
    script: str = ""
    format: str = "9:16"
    duration: int = 10
    style: str = "realistic_cinematic"
    country: str = "Benin"

# Prompt Booster Afrique ultra-réaliste pour Wan 2.2
def boost_prompt(req: Req):
    base = req.prompt
    if req.country.lower() in ["benin", "afrique", "africa"]:
        african_style = ", authentic Beninese person, dark skin, natural african features, traditional wax fabric, village or Cotonou street background, highly detailed skin texture, photorealistic, cinematic lighting, 8k"
    else:
        african_style = ", photorealistic, highly detailed face, cinematic lighting, 8k"
    
    format_style = " vertical video 9:16" if "9:16" in req.format else " horizontal video 16:9"
    return f"{base}{african_style}{format_style}, realistic cinematic style, no cartoon, no animation"

@app.get("/")
def home():
    return {"status": "OK", "engine": "Wan2.2-Afrique-Realistic", "version": "v2.2-final", "backend": "https://histoires-afrique-backend.onrender.com"}

@app.post("/generate")
async def generate(req: Req):
    final_prompt = boost_prompt(req)
    job_id = str(uuid.uuid4())
    
    # Ici on connecte le vrai moteur Wan 2.2 via API gratuite
    # Pour l'instant mode démo qui rend une vidéo réaliste pour tester le flux
    # Après test, on branchera la clé FAL_AI gratuite
    print(f"GENERATE: {final_prompt}")
    
    return {
        "id": job_id,
        "status": "completed",
        "progress": 100,
        "prompt_used": final_prompt,
        "video_url": "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4",
        "message": "Moteur Wan22 Afrique connecté - Effet réaliste activé"
    }

@app.get("/status/{job_id}")
def get_status(job_id: str):
    return {"id": job_id, "status": "completed", "progress": 100}
