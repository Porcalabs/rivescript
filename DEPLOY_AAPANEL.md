# Deploy ke VPS aaPanel + Nginx

Panduan ini diasumsikan untuk domain production:

- `https://rivescript.tonglis.com/`

Dan folder project di server:

- `/www/wwwroot/rivescript-app`

## 1. Upload project ke VPS

Pilih salah satu:

```bash
git clone https://github.com/Porcalabs/rivescript.git /www/wwwroot/rivescript-app
```

atau upload file project lewat File Manager aaPanel ke:

```bash
/www/wwwroot/rivescript-app
```

## 2. Upload credential Google Sheets

Pastikan file service account JSON di-upload manual ke:

```bash
/www/wwwroot/rivescript-app/credentials/rivescript-json-account.json
```

Jangan commit file ini ke GitHub.

## 3. Buat file `.env`

Di server, copy contoh env:

```bash
cd /www/wwwroot/rivescript-app
cp .env.example .env
```

Edit `.env` dan isi nilai production:

```env
OPENAI_API_KEY=sk-...
OPENAI_TTS_MODEL=gpt-4o-mini-tts
OPENAI_TTS_VOICE=coral
OPENAI_TTS_INSTRUCTIONS=Speak clearly in a friendly, helpful tone.
GOOGLE_SPREADSHEET_ID=1KlevUWoXXGzq0IE3LHB1OdSa9e06h3PBD-wXec_6t18
SESSION_SECRET_KEY=ganti-dengan-random-panjang
SESSION_COOKIE_SECURE=true
```

`SESSION_SECRET_KEY` bisa dibuat dari:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

## 4. Siapkan virtualenv dan dependency

```bash
cd /www/wwwroot/rivescript-app
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Test app manual dulu

```bash
cd /www/wwwroot/rivescript-app
source .venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8017 --proxy-headers
```

Kalau sukses, cek:

- `http://127.0.0.1:8017/login`

Kalau halaman login muncul, hentikan proses dengan `Ctrl+C`.

## 6. Jalankan sebagai service

### Opsi A: Supervisor di aaPanel

1. Buat folder log:

```bash
mkdir -p /www/wwwroot/rivescript-app/logs
```

2. Di aaPanel buka `App Store` lalu install `Supervisor Manager` jika belum ada.
3. Tambahkan program baru dengan nilai berikut:

- Name: `rivescript`
- Start Command:

```bash
/www/wwwroot/rivescript-app/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8017 --proxy-headers
```

- Run Directory:

```bash
/www/wwwroot/rivescript-app
```

4. Simpan lalu start service.

Alternatifnya, pakai file contoh:

- [deploy/supervisor-rivescript.conf](/D:/2%20Cari%20Wang/Mr%20titis/Doktoral/rivescript-chatboot-web-app-main/deploy/supervisor-rivescript.conf)

### Opsi B: systemd

Kalau kamu lebih nyaman pakai SSH:

```bash
cp /www/wwwroot/rivescript-app/deploy/rivescript.service /etc/systemd/system/rivescript.service
systemctl daemon-reload
systemctl enable rivescript
systemctl start rivescript
systemctl status rivescript
```

Kalau pakai `systemd`, tambahkan env lewat file unit atau `EnvironmentFile`.

## 7. Set reverse proxy di aaPanel

Karena domain `rivescript.tonglis.com` sudah jalan, buka website itu di aaPanel lalu:

1. Masuk ke menu `Reverse Proxy`
2. Klik `Add Reverse Proxy`
3. Isi target:

```text
http://127.0.0.1:8017
```

4. Simpan dan aktifkan

Kalau mau pakai config manual, contoh ada di:

- [deploy/nginx-rivescript.tonglis.com.conf](/D:/2%20Cari%20Wang/Mr%20titis/Doktoral/rivescript-chatboot-web-app-main/deploy/nginx-rivescript.tonglis.com.conf)

## 8. Aktifkan SSL

Di aaPanel:

1. Buka website `rivescript.tonglis.com`
2. Masuk ke menu `SSL`
3. Pilih `Let's Encrypt`
4. Issue certificate
5. Aktifkan `Force HTTPS`

Setelah HTTPS aktif, `SESSION_COOKIE_SECURE=true` akan membuat session cookie lebih aman.

## 9. Verifikasi setelah publish

Cek ini satu per satu:

1. `https://rivescript.tonglis.com/login` bisa dibuka
2. Register user baru berhasil
3. Login berhasil
4. Tombol `Done` mengubah progress
5. Data `users` dan `progress` masuk ke Google Sheets
6. Chat menghasilkan audio

## 10. Update aplikasi nanti

Kalau deploy lewat Git:

```bash
cd /www/wwwroot/rivescript-app
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
```

Lalu restart service dari aaPanel atau:

```bash
supervisorctl restart rivescript
```

atau:

```bash
systemctl restart rivescript
```

## Troubleshooting cepat

Kalau login/register gagal:

- cek file `.env`
- cek file credentials JSON ada di folder `credentials/`
- cek spreadsheet masih dishare ke service account

Kalau audio tidak keluar:

- cek `OPENAI_API_KEY`
- cek VPS bisa akses internet keluar ke `443`

Kalau domain tidak membuka app:

- cek reverse proxy aaPanel
- cek service Uvicorn hidup di port `8017`
- cek firewall VPS
