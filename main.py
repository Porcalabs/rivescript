import os
import tempfile
import uuid

import edge_tts
from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from rivescript import RiveScript

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TMP_DIR = os.path.join(tempfile.gettempdir(), "rivescript-chatbot-audio")
VOICE_CANDIDATES = [
    "id-ID-GadisNeural",
    "id-ID-ArdiNeural",
    "en-US-JennyNeural",
    "en-US-AriaNeural",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup folders
bot = RiveScript()
# bot.load_directory("./bot")
bot.load_file("./bot/brain_1.rive")
bot.sort_replies()

app.mount("/static", StaticFiles(directory="static"), name="static")
# app.mount("/tmp", StaticFiles(directory="tmp"), name="tmp")
templates = Jinja2Templates(directory="templates")

os.makedirs(TMP_DIR, exist_ok=True)


async def generate_audio(reply: str):
    audio_filename = f"{uuid.uuid4().hex}.mp3"
    audio_file = os.path.join(TMP_DIR, audio_filename)
    errors = []

    for voice in VOICE_CANDIDATES:
        try:
            communicate = edge_tts.Communicate(reply, voice=voice)
            await communicate.save(audio_file)
            return f"/audio/{audio_filename}?nocache={os.urandom(4).hex()}", None
        except Exception as exc:
            errors.append(f"{voice}: {exc}")
            if os.path.exists(audio_file):
                try:
                    os.remove(audio_file)
                except OSError:
                    pass

    print("Audio generation error:", " | ".join(errors))
    return None, "Audio tidak tersedia untuk respons ini."


@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    content = None
    with open("./bot/brain_1.rive", "r", encoding="utf-8") as file:
        content = file.read()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"rivescript_text": content},
    )


@app.post("/set-rivescript")
async def set_rivescript(rivescript: str = Form(...)):
    global bot
    bot = RiveScript()
    bot.stream(rivescript)
    bot.sort_replies()


@app.post("/chat", response_class=HTMLResponse)
async def chat(request: Request, message: str = Form(...)):
    reply = bot.reply("localuser", message)
    audio_url, audio_error = await generate_audio(reply)

    return templates.TemplateResponse(
        request=request,
        name="chat_response.html",
        context={
            "message": message,
            "reply": reply,
            "audio_url": audio_url,
            "audio_error": audio_error,
        },
    )


@app.get("/audio/{audio_filename}")
async def get_audio(audio_filename: str):
    audio_file = os.path.join(TMP_DIR, audio_filename)
    if os.path.exists(audio_file):
        return FileResponse(audio_file, media_type="audio/mpeg", filename=audio_filename)
    return {"error": "Audio not found"}
