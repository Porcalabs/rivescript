import os
import tempfile
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import gspread
from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openai import AsyncOpenAI
from passlib.context import CryptContext
from rivescript import RiveScript
from starlette.middleware.sessions import SessionMiddleware


for proxy_name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
    proxy_value = os.getenv(proxy_name, "")
    if "127.0.0.1:9" in proxy_value or "localhost:9" in proxy_value:
        os.environ.pop(proxy_name, None)

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
TMP_DIR = Path(tempfile.gettempdir()) / "rivescript-chatbot-audio"
CREDENTIALS_FILE = BASE_DIR / "credentials" / "rivescript-json-account.json"
SPREADSHEET_ID = os.getenv(
    "GOOGLE_SPREADSHEET_ID",
    "1KlevUWoXXGzq0IE3LHB1OdSa9e06h3PBD-wXec_6t18",
)
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "porcalabs-rivescript-dev-secret")
OPENAI_TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
OPENAI_TTS_VOICE = os.getenv("OPENAI_TTS_VOICE", "coral")
OPENAI_TTS_INSTRUCTIONS = os.getenv(
    "OPENAI_TTS_INSTRUCTIONS",
    "Speak clearly in a friendly, helpful tone.",
)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    session_cookie="rivescript_session",
    same_site="lax",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup folders
bot = RiveScript()
bot.load_file("./bot/brain_1.rive")
bot.sort_replies()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
TMP_DIR.mkdir(parents=True, exist_ok=True)


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def normalize_bool(value):
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def compile_bot(rivescript_text: str):
    new_bot = RiveScript()
    new_bot.stream(rivescript_text)
    new_bot.sort_replies()
    return new_bot


def get_default_script():
    return (BASE_DIR / "bot" / "brain_1.rive").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def get_gspread_client():
    return gspread.service_account(filename=str(CREDENTIALS_FILE))


def get_spreadsheet():
    return get_gspread_client().open_by_key(SPREADSHEET_ID)


def get_worksheet(name: str):
    return get_spreadsheet().worksheet(name)


def get_active_universities():
    rows = get_worksheet("universities").get_all_records()
    universities = [row for row in rows if normalize_bool(row.get("is_active", True))]
    if not any(row.get("university_id") in {"OTHER", "OTH"} for row in universities):
        universities.append(
            {
                "university_id": "OTHER",
                "university_name": "Lainnya",
                "registration_code": "",
                "is_active": True,
            }
        )
    return universities


def get_real_university_rows():
    rows = get_worksheet("universities").get_all_records()
    return [row for row in rows if normalize_bool(row.get("is_active", True))]


def get_user_row_by_id(user_id: str):
    rows = get_worksheet("users").get_all_records()
    for row in rows:
        if row.get("user_id") == user_id and normalize_bool(row.get("is_active", True)):
            return row
    return None


def get_user_row_by_login(nim: str, university_id: str):
    rows = get_worksheet("users").get_all_records()
    for row in rows:
        if (
            str(row.get("nim", "")).strip() == nim.strip()
            and str(row.get("university_id", "")).strip() == university_id.strip()
            and normalize_bool(row.get("is_active", True))
        ):
            return row
    return None


def university_name_for_user(user_row):
    university_id = user_row.get("university_id", "")
    if university_id in {"OTHER", "OTH"}:
        return user_row.get("university_other_name") or "Lainnya"
    for university in get_real_university_rows():
        if university.get("university_id") == university_id:
            return university.get("university_name", university_id)
    return university_id


def validate_registration_code(university_id: str, code: str):
    code = code.strip()
    for university in get_real_university_rows():
        row_id = str(university.get("university_id", "")).strip()
        row_code = str(university.get("registration_code", "")).strip()
        if university_id in {"OTHER", "OTH"}:
            if row_id in {"OTHER", "OTH"} and row_code == code:
                return True
        elif row_id == university_id and row_code == code:
            return True
    return False


def append_user(full_name, nim, university_id, other_name, password):
    users_ws = get_worksheet("users")
    user_id = uuid.uuid4().hex
    password_hash = pwd_context.hash(password)
    now = utc_now_iso()
    users_ws.append_row(
        [
            user_id,
            full_name,
            nim,
            university_id,
            other_name,
            password_hash,
            now,
            "",
            "TRUE",
        ],
        value_input_option="USER_ENTERED",
    )
    return user_id


def update_last_login(user_id: str):
    users_ws = get_worksheet("users")
    values = users_ws.get_all_values()
    if not values:
        return
    headers = values[0]
    last_login_index = headers.index("last_login_at") + 1
    for row_number, row in enumerate(values[1:], start=2):
        if row and row[0] == user_id:
            users_ws.update_cell(row_number, last_login_index, utc_now_iso())
            return


def get_progress_records_for_user(user_id: str):
    progress_rows = get_worksheet("progress").get_all_records()
    return [row for row in progress_rows if row.get("user_id") == user_id]


def upsert_progress(user_id: str, unit_id: str, unit_name: str, status: str):
    progress_ws = get_worksheet("progress")
    values = progress_ws.get_all_values()
    headers = values[0] if values else []
    now = utc_now_iso()

    for row_number, row in enumerate(values[1:], start=2):
        if len(row) >= 3 and row[1] == user_id and row[2] == unit_id:
            completed_at = now if status == "done" else ""
            progress_ws.update(
                f"D{row_number}:G{row_number}",
                [[unit_name, status, completed_at, now]],
                value_input_option="USER_ENTERED",
            )
            return

    progress_ws.append_row(
        [
            uuid.uuid4().hex,
            user_id,
            unit_id,
            unit_name,
            status,
            now if status == "done" else "",
            now,
        ],
        value_input_option="USER_ENTERED",
    )


def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return get_user_row_by_id(user_id)


def auth_context(request: Request):
    return {
        "request": request,
        "universities": get_active_universities(),
        "error": None,
        "form_data": {},
    }


async def generate_audio(reply: str):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, "Audio tidak tersedia karena OPENAI_API_KEY belum dikonfigurasi."

    audio_filename = f"{uuid.uuid4().hex}.mp3"
    audio_file = TMP_DIR / audio_filename

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
        if audio_file.exists():
            try:
                audio_file.unlink()
            except OSError:
                pass
        print(f"Audio generation error: {exc}")
        return None, "Audio gagal dibuat oleh provider TTS."


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if get_current_user(request):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html", context=auth_context(request))


@app.post("/login", response_class=HTMLResponse)
async def login_user(
    request: Request,
    university_id: str = Form(...),
    nim: str = Form(...),
    password: str = Form(...),
):
    context = auth_context(request)
    context["form_data"] = {"university_id": university_id, "nim": nim}

    user_row = get_user_row_by_login(nim, university_id)
    if not user_row or not pwd_context.verify(password, user_row.get("password_hash", "")):
        context["error"] = "Login gagal. Periksa universitas, NIM, dan password."
        return templates.TemplateResponse(request=request, name="login.html", context=context, status_code=400)

    request.session["user_id"] = user_row["user_id"]
    update_last_login(user_row["user_id"])
    return RedirectResponse("/", status_code=303)


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    if get_current_user(request):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request=request, name="register.html", context=auth_context(request))


@app.post("/register", response_class=HTMLResponse)
async def register_user(
    request: Request,
    full_name: str = Form(...),
    nim: str = Form(...),
    university_id: str = Form(...),
    university_other_name: str = Form(""),
    registration_code: str = Form(...),
    password: str = Form(...),
):
    context = auth_context(request)
    context["form_data"] = {
        "full_name": full_name,
        "nim": nim,
        "university_id": university_id,
        "university_other_name": university_other_name,
    }

    if university_id in {"OTHER", "OTH"} and not university_other_name.strip():
        context["error"] = "Jika memilih Lainnya, nama universitas wajib diisi."
        return templates.TemplateResponse(request=request, name="register.html", context=context, status_code=400)

    if len(password) < 6:
        context["error"] = "Password minimal 6 karakter."
        return templates.TemplateResponse(request=request, name="register.html", context=context, status_code=400)

    if not validate_registration_code(university_id, registration_code):
        context["error"] = "Kode universitas tidak valid."
        return templates.TemplateResponse(request=request, name="register.html", context=context, status_code=400)

    if get_user_row_by_login(nim, university_id):
        context["error"] = "NIM tersebut sudah terdaftar pada universitas yang dipilih."
        return templates.TemplateResponse(request=request, name="register.html", context=context, status_code=400)

    user_id = append_user(
        full_name=full_name.strip(),
        nim=nim.strip(),
        university_id=university_id.strip(),
        other_name=university_other_name.strip(),
        password=password,
    )
    request.session["user_id"] = user_id
    update_last_login(user_id)
    return RedirectResponse("/", status_code=303)


@app.post("/logout")
async def logout_user(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "rivescript_text": get_default_script(),
            "current_user": current_user,
            "current_university_name": university_name_for_user(current_user),
        },
    )


@app.get("/progress")
async def get_progress(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse({"ok": False, "message": "Unauthorized"}, status_code=401)

    progress_map = {
        row.get("unit_id"): row.get("status", "not_started")
        for row in get_progress_records_for_user(current_user["user_id"])
    }
    return JSONResponse({"ok": True, "progress": progress_map})


@app.post("/progress")
async def update_progress(
    request: Request,
    unit_id: str = Form(...),
    unit_name: str = Form(...),
    status: str = Form(...),
):
    current_user = get_current_user(request)
    if not current_user:
        return JSONResponse({"ok": False, "message": "Unauthorized"}, status_code=401)

    if status not in {"not_started", "in_progress", "done"}:
        return JSONResponse({"ok": False, "message": "Status tidak valid."}, status_code=400)

    upsert_progress(current_user["user_id"], unit_id, unit_name, status)
    return JSONResponse({"ok": True})


@app.post("/set-rivescript")
async def set_rivescript(request: Request, rivescript: str = Form(...)):
    if not get_current_user(request):
        return JSONResponse({"ok": False, "message": "Unauthorized"}, status_code=401)

    global bot
    try:
        bot = compile_bot(rivescript)
        return JSONResponse({"ok": True, "message": "Script applied successfully."})
    except Exception as exc:
        return JSONResponse(
            {"ok": False, "message": f"RiveScript error: {exc}"},
            status_code=400,
        )


@app.post("/chat", response_class=HTMLResponse)
async def chat(request: Request, message: str = Form(...)):
    current_user = get_current_user(request)
    if not current_user:
        return HTMLResponse("Unauthorized", status_code=401)

    reply = bot.reply(current_user["user_id"], message)
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
    audio_file = TMP_DIR / audio_filename
    if audio_file.exists():
        return FileResponse(audio_file, media_type="audio/mpeg", filename=audio_filename)
    return {"error": "Audio not found"}
