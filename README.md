# BSUI2 Messenger Server

Serwer komunikatora: HTTPS (REST) + WSS, port **2137**.

## Uruchomienie

Python 3.12+, OpenSSL (albo Git for Windows z openssl).

### Certyfikaty

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File scripts/gen_certs.ps1
```

```bash
# Linux/macOS / Git Bash
bash scripts/gen_certs.sh
```

### Z `uv`

```bash
cd bsui2-server
uv sync
uv run uvicorn bsui2_server.main:app --host 0.0.0.0 --port 2137 \
  --ssl-certfile certs/cert.pem --ssl-keyfile certs/key.pem
```

Albo: `uv run bsui2-server` (TLS włącza się, gdy istnieją `certs/cert.pem` i `certs/key.pem`).

### Bez `uv` (venv + pip)

```bash
cd bsui2-server
python -m venv .venv
```

Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn bsui2_server.main:app --host 0.0.0.0 --port 2137 `
  --ssl-certfile certs/cert.pem --ssl-keyfile certs/key.pem
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
uvicorn bsui2_server.main:app --host 0.0.0.0 --port 2137 \
  --ssl-certfile certs/cert.pem --ssl-keyfile certs/key.pem
```

Albo po aktywacji venv: `bsui2-server`.

Certyfikat jest self-signed — klient musi zaufać `certs/cert.pem` albo (w labie) wyłączyć weryfikację TLS.

### Zmienne środowiskowe

| Zmienna | Domyślnie |
|---------|-----------|
| `BSUI2_PORT` | `2137` |
| `BSUI2_HOST` | `0.0.0.0` |
| `BSUI2_DATABASE_URL` | SQLite w `data/bsui2.db` |
| `BSUI2_SSL_CERTFILE` | `certs/cert.pem` |
| `BSUI2_SSL_KEYFILE` | `certs/key.pem` |

---

## API

Baza: `https://<host>:2137`. Body w JSON. Autoryzacja REST: nagłówek `Authorization: Bearer <token>`.

Jedna sesja na użytkownika — ponowne logowanie unieważnia stary token i zamyka stare WebSockety.

| Method | Path | Auth | Opis |
|--------|------|------|------|
| POST | `/register` | — | `{login, password}` → `{status:"ok"}` / `409` jeśli zajęty |
| POST | `/login` | — | `{login, password}` → `{token}` / `401` |
| POST | `/create` | Bearer | `{name}` → `{id}` |
| GET | `/my_rooms` | Bearer | lista pokoi (+ alias `/myrooms`) |
| POST | `/invite/{id}` | Bearer | `{users:[...]}` → `{kod:"ok"}` |
| GET | `/get_msg/{id}` | Bearer | historia; opcjonalnie `?limit=` (1–1000, domyślnie 100) |
| GET | `/is_active/{login}` | — | `{login, active}` |
| WS | `/ws/{id}?token=` | query | czat na żywo |
| GET | `/health` | — | `{status:"ok"}` |

Przykład pokoju z `/my_rooms`:

```json
{"rooms":[{"id":"...","name":"lab","is_group":true,"users":["ania","janek"]}]}
```

Ramka wiadomości (historia i broadcast WS):

```json
{"Timestamp":"2026-10-29T18:39:00+00:00","who":"janek","message":"cześć"}
```

---

## Jak zbudować klienta

### 1. Rejestracja i logowanie

```http
POST /register   {"login":"janek","password":"haslo"}
POST /login      {"login":"janek","password":"haslo"}  →  zapisz token
```

### 2. Pokoje

- `GET /my_rooms` — pokaż listę (`id`, `name`, `users`)
- `POST /create` z `{name}` — twórca jest od razu członkiem
- `POST /invite/{id}` z `{users:["ania"]}` — zaprasza istniejące loginy (tylko członek pokoju)

### 3. Wejście do pokoju

1. `GET /get_msg/{id}` — narysuj historię (kolejność od najstarszej)
2. Połącz WebSocket:

```text
wss://<host>:2137/ws/{id}?token=<token>
```

- **wysyłaj:** `{"message":"treść"}`
- **odbieraj:** pełne ramki `{Timestamp, who, message}` (także własne — serwer rozsyła do wszystkich w pokoju)

Błędny JSON na WS → serwer odsyła `{"error":"..."}` i nie zamyka połączenia.

### 4. Sesja i błędy

| Sytuacja | Objaw | Reakcja klienta |
|----------|--------|-----------------|
| Ponowne logowanie tym samym kontem | REST `401`, WS close `4001` | wyloguj, wróć do logowania |
| Brak członkostwa | REST `403`, WS close `4403` | odśwież listę pokoi |
| Zły/brak tokena przy WS | close `4401` | zaloguj ponownie |

Opcjonalnie: `GET /is_active/{login}` — czy ktoś jest zalogowany / ma otwarty WS.

### Flow UI

```text
login/register → lista pokoi → otwarcie pokoju (historia + WS) → wyjście do listy
```
