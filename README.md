# RiveScript Learning Lab

Web app pembelajaran RiveScript berbasis FastAPI, Google Sheets, dan OpenAI TTS.

## Menjalankan lokal

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

## Deploy ke VPS aaPanel

Panduan production ada di:

- [DEPLOY_AAPANEL.md](/D:/2%20Cari%20Wang/Mr%20titis/Doktoral/rivescript-chatboot-web-app-main/DEPLOY_AAPANEL.md)
