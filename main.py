import os
import uuid
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from gtts import gTTS


# ============================================================
# HISTOIRES D'AFRIQUE AI
# Backend principal
# ============================================================

app = FastAPI(
    title="Histoires d’Afrique AI",
    description="Backend de génération de vidéos réalistes africaines",
    version="2.0.0"
)


# ============================================================
# CORS
# Permet à l'application HTML/APK de communiquer avec le backend
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DOSSIERS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio"
AUDIO_DIR.mkdir(exist_ok=True)


# ============================================================
# CONFIGURATION DU MOTEUR VIDEO
#
# Plus tard, nous mettrons ici l'adresse du véritable service
# Wan 2.2 ou d'un autre moteur vidéo.
#
# NE METS JAMAIS une clé secrète dans le HTML de l'application.
# ============================================================

VIDEO_PROVIDER_URL = os.getenv("VIDEO_PROVIDER_URL", "").strip()
VIDEO_PROVIDER_KEY = os.getenv("VIDEO_PROVIDER_KEY", "").strip()


# ============================================================
# STOCKAGE TEMPORAIRE DES TACHES
#
# Pour commencer, les tâches sont conservées en mémoire.
# Plus tard, on pourra utiliser une vraie base de données.
# ============================================================

VIDEO_JOBS = {}


# ============================================================
# MODELES DE DONNEES
# ============================================================

class VideoRequest(BaseModel):
    # Texte de l'histoire / scénario
    script: str = Field(default="", max_length=20000)

    # Langue
    lang: str = "fr"

    # Personnages
    perso: str = ""

    # Duo / description principale
    duo: str = ""

    # Pays africain
    country: str = "Bénin"

    # Style visuel
    style: str = "realistic_cinematic"

    # Format vidéo
    format: str = "9:16"

    # Durée demandée
    duration: int = 10

    # Voix
    voice: str = "narrateur"

    # Mouvement
    motion: str = "natural"

    # Description des animaux éventuels
    animals: str = ""

    # Description des scènes
    scenes: str = ""

    # Musique
    music: bool = True


# ============================================================
# OUTILS
# ============================================================

def normalize_language(language: str) -> str:
    """
    Transforme par exemple :
    fr-FR -> fr
    en-US -> en
    """
    language = (language or "fr").lower().strip()

    code = language.split("-")[0]

    allowed = {
        "fr",
        "en",
        "es",
        "de",
        "it",
        "pt",
        "nl"
    }

    if code not in allowed:
        return "fr"

    return code


def build_video_prompt(req: VideoRequest) -> str:
    """
    Construit le prompt destiné au futur moteur vidéo IA.
    """

    prompt = f"""
Créer une vidéo {req.style} et cinématographique.

CONTEXTE :
Pays africain : {req.country}

PERSONNAGES :
{req.perso}

SCENARIO :
{req.script}

DUO / INTERACTION :
{req.duo}

ANIMAUX :
{req.animals}

SCENES :
{req.scenes}

MOUVEMENTS :
{req.motion}

EXIGENCES VISUELLES :
- personnages humains réalistes
- apparence cohérente entre les scènes
- mouvements naturels du corps
- marche naturelle
- gestes naturels
- mouvements de tête
- mouvements des yeux
- expressions faciales crédibles
- interactions naturelles entre les personnages
- mouvements naturels des animaux
- caméra cinématographique
- lumière naturelle
- environnement africain crédible
- profondeur de champ réaliste
- continuité visuelle entre les scènes
- rendu immersif et réaliste

DIALOGUE ET VOIX :
- voix adaptées aux personnages
- dialogue naturel
- synchronisation des lèvres avec les paroles lorsque le moteur le permet
- expressions correspondant aux émotions

FORMAT :
{req.format}

DUREE :
{req.duration} secondes

LANGUE :
{req.lang}

La vidéo doit être originale et ne doit pas copier une personne,
une œuvre, une marque ou une vidéo existante.
"""

    return prompt.strip()


def create_audio(req: VideoRequest) -> str:
    """
    Génère une narration audio avec gTTS.
    """

    language = normalize_language(req.lang)

    text = req.script.strip()

    if not text:
        text = "Bienvenue dans Histoires d’Afrique AI."

    # gTTS peut échouer sur certains environnements réseau.
    filename = f"{uuid.uuid4()}.mp3"
    filepath = AUDIO_DIR / filename

    slow = False

    if "lent" in req.voice.lower():
        slow = True

    tts = gTTS(
        text=text[:5000],
        lang=language,
        slow=slow
    )

    tts.save(str(filepath))

    return filename


def provider_is_configured() -> bool:
    """
    Vérifie si un véritable fournisseur vidéo est configuré.
    """
    return bool(VIDEO_PROVIDER_URL)


def send_to_video_provider(payload: dict):
    """
    Envoie une demande au moteur vidéo configuré.

    Le fournisseur devra exposer un endpoint /generate.

    Exemple :
    VIDEO_PROVIDER_URL=https://mon-serveur-video.com

    Le backend appellera :
    https://mon-serveur-video.com/generate
    """

    if not VIDEO_PROVIDER_URL:
        return None

    url = VIDEO_PROVIDER_URL.rstrip("/") + "/generate"

    headers = {
        "Content-Type": "application/json"
    }

    if VIDEO_PROVIDER_KEY:
        headers["Authorization"] = f"Bearer {VIDEO_PROVIDER_KEY}"

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read().decode("utf-8")

            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {
                    "raw_response": raw
                }

    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="ignore")

        raise HTTPException(
            status_code=502,
            detail=f"Le moteur vidéo a retourné une erreur : {body}"
        )

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Impossible de contacter le moteur vidéo : {str(error)}"
        )


# ============================================================
# ROUTE PRINCIPALE
# ============================================================

@app.get("/")
def home():
    return {
        "status": "OK",
        "app": "Histoires d’Afrique AI",
        "backend": "FastAPI",
        "version": "2.0.0",
        "video_engine_configured": provider_is_configured()
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "video_engine_configured": provider_is_configured(),
        "audio": "gTTS"
    }


# ============================================================
# GENERATION PRINCIPALE
# ============================================================

@app.post("/generate")
def generate_video(req: VideoRequest):
    """
    Endpoint compatible avec l'ancienne application.
    """

    return start_generation(req)


# ============================================================
# NOUVEL ENDPOINT VIDEO
# ============================================================

@app.post("/video/generate")
def video_generate(req: VideoRequest):
    """
    Endpoint utilisé par notre nouvelle application HTML.
    """

    return start_generation(req)


# ============================================================
# LANCEMENT DE GENERATION
# ============================================================

def start_generation(req: VideoRequest):

    job_id = str(uuid.uuid4())

    # --------------------------------------------------------
    # Prompt vidéo
    # --------------------------------------------------------

    video_prompt = build_video_prompt(req)

    # --------------------------------------------------------
    # Audio
    # --------------------------------------------------------

    audio_filename = None

    try:
        audio_filename = create_audio(req)
    except Exception as error:
        print("Erreur audio :", error)

    # --------------------------------------------------------
    # Création de la tâche
    # --------------------------------------------------------

    VIDEO_JOBS[job_id] = {
        "id": job_id,
        "status": "created",
        "progress": 5,
        "video_url": None,
        "audio_url": (
            f"/audio/{audio_filename}"
            if audio_filename
            else None
        ),
        "prompt": video_prompt,
        "country": req.country,
        "format": req.format,
        "duration": req.duration
    }

    # --------------------------------------------------------
    # Si aucun moteur vidéo n'est encore configuré
    # --------------------------------------------------------

    if not provider_is_configured():

        VIDEO_JOBS[job_id]["status"] = "waiting_for_video_engine"
        VIDEO_JOBS[job_id]["progress"] = 10

        return {
            "success": True,
            "job_id": job_id,
            "status": "waiting_for_video_engine",
            "message": (
                "Le backend fonctionne, mais aucun moteur vidéo IA "
                "n'est encore connecté."
            ),
            "audio_url": (
                f"/audio/{audio_filename}"
                if audio_filename
                else None
            ),
            "image_prompt": video_prompt
        }

    # --------------------------------------------------------
    # Envoi au véritable moteur vidéo
    # --------------------------------------------------------

    provider_payload = {
        "prompt": video_prompt,
        "script": req.script,
        "country": req.country,
        "style": req.style,
        "format": req.format,
        "duration": req.duration,
        "language": req.lang,
        "voice": req.voice,
        "motion": req.motion,
        "animals": req.animals,
        "scenes": req.scenes,
        "audio_url": (
            f"/audio/{audio_filename}"
            if audio_filename
            else None
        )
    }

    provider_result = send_to_video_provider(provider_payload)

    if not provider_result:
        raise HTTPException(
            status_code=502,
            detail="Le moteur vidéo n'a pas répondu."
        )

    # --------------------------------------------------------
    # Récupération de l'identifiant de tâche du fournisseur
    # --------------------------------------------------------

    provider_task_id = (
        provider_result.get("id")
        or provider_result.get("task_id")
        or provider_result.get("job_id")
    )

    VIDEO_JOBS[job_id]["status"] = "processing"
    VIDEO_JOBS[job_id]["progress"] = 15
    VIDEO_JOBS[job_id]["provider_task_id"] = provider_task_id
    VIDEO_JOBS[job_id]["provider_response"] = provider_result

    # Si le fournisseur donne déjà directement une vidéo
    video_url = (
        provider_result.get("video_url")
        or provider_result.get("url")
    )

    if video_url:
        VIDEO_JOBS[job_id]["status"] = "completed"
        VIDEO_JOBS[job_id]["progress"] = 100
        VIDEO_JOBS[job_id]["video_url"] = video_url

    return {
        "success": True,
        "job_id": job_id,
        "status": VIDEO_JOBS[job_id]["status"],
        "progress": VIDEO_JOBS[job_id]["progress"],
        "video_url": VIDEO_JOBS[job_id]["video_url"],
        "audio_url": VIDEO_JOBS[job_id]["audio_url"]
    }


# ============================================================
# ETAT D'UNE VIDEO
# ============================================================

@app.get("/video/status/{job_id}")
def video_status(job_id: str):

    job = VIDEO_JOBS.get(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Tâche vidéo introuvable."
        )

    return job


# ============================================================
# ANCIEN FORMAT DE STATUS
# ============================================================

@app.get("/status/{job_id}")
def old_status(job_id: str):

    return video_status(job_id)


# ============================================================
# AUDIO
# ============================================================

@app.get("/audio/{name}")
def get_audio(name: str):

    # Protection simple contre les chemins dangereux
    safe_name = Path(name).name

    filepath = AUDIO_DIR / safe_name

    if not filepath.exists():
        raise HTTPException(
            status_code=404,
            detail="Fichier audio introuvable."
        )

    return FileResponse(
        str(filepath),
        media_type="audio/mpeg"
    )


# ============================================================
# INFORMATIONS DU MOTEUR VIDEO
# ============================================================

@app.get("/video/engine")
def video_engine():

    if provider_is_configured():
        return {
            "configured": True,
            "message": "Un moteur vidéo est configuré."
        }

    return {
        "configured": False,
        "message": (
            "Aucun moteur vidéo IA n'est encore configuré. "
            "Le backend est prêt à recevoir Wan 2.2 ou un autre moteur."
        )
    }


# ============================================================
# SUPPRESSION D'UNE TACHE
# ============================================================

@app.delete("/video/{job_id}")
def delete_video_job(job_id: str):

    if job_id not in VIDEO_JOBS:
        raise HTTPException(
            status_code=404,
            detail="Tâche introuvable."
        )

    del VIDEO_JOBS[job_id]

    return {
        "success": True,
        "message": "Tâche supprimée."
    }
