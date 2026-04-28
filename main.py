import os
import tempfile
import uuid

from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openai import AsyncOpenAI
from rivescript import RiveScript

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TMP_DIR = os.path.join(tempfile.gettempdir(), "rivescript-chatbot-audio")
OPENAI_TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
OPENAI_TTS_VOICE = os.getenv("OPENAI_TTS_VOICE", "coral")
OPENAI_TTS_INSTRUCTIONS = os.getenv(
    "OPENAI_TTS_INSTRUCTIONS",
    "Speak clearly in a friendly, helpful tone.",
)

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
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, "Audio tidak tersedia karena OPENAI_API_KEY belum dikonfigurasi."

    audio_filename = f"{uuid.uuid4().hex}.mp3"
    audio_file = os.path.join(TMP_DIR, audio_filename)

    try:
        openai_client = AsyncOpenAI(api_key=api_key)
        async with openai_client.audio.speech.with_streaming_response.create(
            model=OPENAI_TTS_MODEL,
            voice=OPENAI_TTS_VOICE,
            input=reply,
            instructions=OPENAI_TTS_INSTRUCTIONS,
            response_format="mp3",
        ) as response:
            await response.stream_to_file(audio_file)
        return f"/audio/{audio_filename}?nocache={os.urandom(4).hex()}", None
    except Exception as exc:
        if os.path.exists(audio_file):
            try:
                os.remove(audio_file)
            except OSError:
                pass
        print(f"Audio generation error: {exc}")
        return None, "Audio gagal dibuat oleh provider TTS."


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
    try:
        new_bot = RiveScript()
        new_bot.stream(rivescript)
        new_bot.sort_replies()
        bot = new_bot
        return JSONResponse({"ok": True, "message": "Script applied successfully."})
    except Exception as exc:
        return JSONResponse(
            {"ok": False, "message": f"RiveScript error: {exc}"},
            status_code=400,
        )


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
