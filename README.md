#[README.md]
# OXNET v1.1 Beta — Light VLESS Admin Panel

This update enables **Beta for everyone** and keeps the app focused on the transports that work in this runtime:

- **VLESS / WebSocket**
- **VLESS / XHTTP**
- **WS + XHTTP bundle**

## What changed in v1.1 Beta

- All existing configs are migrated to `beta: true` on startup.
- All new configs are created as Beta automatically.
- Added `POST /api/beta/all` to mark every config as Beta immediately.
- Added `GET /api/system/info` for diagnostics/version/protocol info.
- Dashboard now shows Beta status and includes a “Beta for everyone” action.
- App version is now `1.1-beta`.
- Per-config editable paths remain supported:
  - WS: `/ws/my-user-path`
  - XHTTP: `/xhttp-oxnet/packet-up/my-user-path/...`

## Run

```bash
pip install -r requirements.txt
python main.py
```

Open `http://localhost:8000/dashboard`. Default password is `OXNET` unless `ADMIN_PASSWORD` is set.

## Environment

| Variable | Purpose | Default |
| --- | --- | --- |
| `PORT` | HTTP port | `8000` |
| `ADMIN_PASSWORD` | Web dashboard password | `OXNET` |
| `SECRET_KEY` | Session/password salt | auto generated |
| `DATA_DIR` | Persistent state folder | `./data` |
| `XHTTP_BASE_PATH` | XHTTP route base | `/xhttp-oxnet` |
| `BETA_ALL` | Force all configs into Beta | `1` |

## Notes

Path slugs are restricted to letters, numbers, dash, underscore and dot. Non-working proxy types remain removed from the admin experience.
