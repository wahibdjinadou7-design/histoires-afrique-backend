from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from gtts import gTTS
import uuid

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class VideoRequest(BaseModel):
    duo: str
    script: str
    lang: str
    perso: str

@app.get("/")
def home():
    return {"status":"OK - Backend Realiste"}

@app.post("/generate")
def generate_video(req: VideoRequest):
    lang_code = req.lang.split("-")[0].lower()
    if lang_code not in ["fr","en","es","de"]: lang_code="fr"
    slow = "vieille" in req.perso.lower() or "vieux" in req.perso.lower()
    filename = f"{uuid.uuid4()}.mp3"
    tts = gTTS(text=req.script[:600], lang=lang_code, slow=slow)
    tts.save(filename)
    prompt = f"{req.duo}, chaise bois cour banco beige Benin, photo realiste 8K TikTok"
    return {"audio_url": f"/audio/{filename}", "image_prompt": prompt, "image_url": f"https://image.pollinations.ai/prompt/{prompt}?width=720&height=900&model=flux-realistic", "duo": req.duo}

@app.get("/audio/{name}")
def get_audio(name: str):
    return FileResponse(name, media_type="audio/mpeg")
