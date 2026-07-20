# main.py
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException, Header
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
import hashlib
import secrets
import base64
import os
import json

from state import (
    load_state, save_state, CONFIG, logger, AUTH,
    LINKS, is_link_allowed, is_ip_allowed, connections, error_logs,
    get_all_links_for_uuid, make_link, remove_link, update_link,
    log_activity, set_first_run_password, is_first_run, DATA_DIR, DATA_FILE
)
from xhttp_siz10 import router as xhttp_router
from relay_protocols import parse_vless_header, parse_trojan_header, check_and_use
from speed_limit import throttle
from pages import DASHBOARD_HTML

try:
    from shadowsocks_server import start_shadowsocks_server
    SS_ENABLED = True
except ImportError:
    SS_ENABLED = False

# ذخیره توکن‌های فعال
active_tokens = {}

def verify_token(authorization: str = Header(None)):
    """بررسی توکن از هدر Authorization"""
    # اگر رمز تنظیم نشده، اجازه دسترسی بده
    if is_first_run():
        return True
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        token = authorization
    
    if token not in active_tokens:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if active_tokens[token] < datetime.now():
        del active_tokens[token]
        raise HTTPException(status_code=401, detail="Token expired")
    
    return True

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting OXNet Core Server (Multi-Protocol Edition)...")
    
    # بارگذاری وضعیت
    await load_state()
    
    # بررسی وضعیت اولین اجرا
    if is_first_run():
        logger.info("⚠️ FIRST RUN: No password set! Please set a password via the setup page.")
        print("\n" + "="*60)
        print("⚠️  FIRST RUN DETECTED - No password is set!")
        print("🔑 Please visit the panel and set your password.")
        print("📁 Data file:", DATA_FILE)
        print("="*60 + "\n")
    else:
        logger.info("✅ Password is set. Panel is secured.")
    
    # اجرای تسک پس‌زمینه سرور شادوساکس
    if SS_ENABLED:
        from state import SS_PORT
        asyncio.create_task(start_shadowsocks_server(SS_PORT))
        
    yield
    
    logger.info("Shutting down OXNet Core...")
    await save_state()

app = FastAPI(title="OXNet Core", lifespan=lifespan)
app.include_router(xhttp_router)

@app.get("/")
async def root():
    return HTMLResponse(DASHBOARD_HTML)

@app.get("/api/auth/status")
async def auth_status():
    """بررسی وضعیت احراز هویت"""
    return {
        "first_run": is_first_run(),
        "password_set": not is_first_run()
    }

@app.post("/api/auth/setup")
async def setup_password(request: Request):
    """تنظیم رمز عبور برای اولین بار"""
    try:
        data = await request.json()
        password = data.get("password", "")
        confirm = data.get("confirm", "")
    except:
        return JSONResponse({"ok": False, "error": "Invalid request"}, status_code=400)
    
    if len(password) < 6:
        return JSONResponse({"ok": False, "error": "رمز عبور باید حداقل 6 کاراکتر باشد"}, status_code=400)
    
    if password != confirm:
        return JSONResponse({"ok": False, "error": "رمز عبور و تکرار آن مطابقت ندارند"}, status_code=400)
    
    # تنظیم رمز عبور
    success = await set_first_run_password(password)
    if not success:
        return JSONResponse({"ok": False, "error": "خطا در تنظیم رمز عبور"}, status_code=500)
    
    log_activity("auth", "رمز عبور پنل برای اولین بار تنظیم شد", "ok")
    
    # تولید توکن برای لاگین خودکار
    token = secrets.token_urlsafe(32)
    active_tokens[token] = datetime.now().replace(hour=23, minute=59, second=59)
    basic_token = base64.b64encode(f"admin:{token}".encode()).decode()
    
    return {
        "ok": True, 
        "message": "رمز عبور با موفقیت تنظیم شد",
        "token": token,
        "basic_token": basic_token
    }

@app.post("/api/auth/login")
async def login(request: Request):
    """ورود به پنل و دریافت توکن"""
    # اگر رمز تنظیم نشده، خطا بده
    if is_first_run():
        return JSONResponse({
            "ok": False, 
            "error": "رمز عبور تنظیم نشده است. لطفاً ابتدا رمز عبور را تنظیم کنید.",
            "setup_required": True
        }, status_code=400)
    
    try:
        data = await request.json()
        password = data.get("password", "")
    except:
        return JSONResponse({"ok": False, "error": "Invalid request"}, status_code=400)
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if AUTH["password_hash"] != password_hash:
        return JSONResponse({"ok": False, "error": "رمز عبور اشتباه است"}, status_code=401)
    
    # تولید توکن جدید
    token = secrets.token_urlsafe(32)
    active_tokens[token] = datetime.now().replace(hour=23, minute=59, second=59)
    basic_token = base64.b64encode(f"admin:{token}".encode()).decode()
    
    return {
        "ok": True, 
        "token": token,
        "basic_token": basic_token,
        "expires_in": 86400
    }

@app.post("/api/auth/change-password")
async def change_password(request: Request, auth: bool = Depends(verify_token)):
    """تغییر رمز عبور پنل"""
    data = await request.json()
    old_password = data.get("old_password", "")
    new_password = data.get("new_password", "")
    
    if len(new_password) < 6:
        return JSONResponse({"ok": False, "error": "رمز جدید باید حداقل 6 کاراکتر باشد"}, status_code=400)
    
    old_hash = hashlib.sha256(old_password.encode()).hexdigest()
    if AUTH["password_hash"] != old_hash:
        return JSONResponse({"ok": False, "error": "رمز فعلی اشتباه است"}, status_code=401)
    
    AUTH["password_hash"] = hashlib.sha256(new_password.encode()).hexdigest()
    AUTH["password_changed"] = True
    await save_state()
    log_activity("auth", "رمز عبور پنل تغییر کرد", "ok")
    
    return {"ok": True, "message": "رمز عبور با موفقیت تغییر کرد"}

@app.get("/api/auth/default-password")
async def get_default_password():
    """دریافت وضعیت رمز پیش‌فرض"""
    if is_first_run():
        return {"first_run": True, "default_password": None}
    return {"first_run": False, "default_password": None}

@app.get("/api/panel/stats")
async def get_stats(auth: bool = Depends(verify_token)):
    from state import get_system_stats
    total_vol = sum(l.get("used_bytes", 0) for l in LINKS.values())
    return {
        "total_links": len(LINKS),
        "total_traffic_bytes": total_vol,
        "online_users": len(connections),
        "system": get_system_stats(),
        "active_connections": list(connections.values())
    }

@app.get("/api/panel/links")
async def get_links(auth: bool = Depends(verify_token)):
    return {"links": LINKS}

@app.get("/api/panel/links/{uid}")
async def get_link(uid: str, auth: bool = Depends(verify_token)):
    if uid not in LINKS:
        return JSONResponse({"error": "لینک یافت نشد"}, status_code=404)
    return {"link": LINKS[uid]}

@app.put("/api/panel/links/{uid}")
async def edit_link(uid: str, request: Request, auth: bool = Depends(verify_token)):
    if uid not in LINKS:
        return JSONResponse({"error": "لینک یافت نشد"}, status_code=404)
    data = await request.json()
    updated = await update_link(uid, data)
    if not updated:
        return JSONResponse({"error": "خطا در ویرایش"}, status_code=400)
    return {"ok": True, "link": updated}

@app.delete("/api/panel/links/{uid}")
async def del_link(uid: str, auth: bool = Depends(verify_token)):
    res = await remove_link(uid)
    return {"ok": res is not None}

@app.post("/api/panel/multipack")
async def api_create_multipack(request: Request, auth: bool = Depends(verify_token)):
    data = await request.json()
    label = data.get("label", "MultiPack")
    limit_bytes = int(data.get("limit_gb", 0) * 1024**3)
    days = int(data.get("days", 0))
    
    expires_at = None
    from datetime import timedelta
    if days > 0:
        expires_at = (datetime.now() + timedelta(days=days)).isoformat()
        
    uid, link = await make_link(label=label, limit_bytes=limit_bytes, expires_at=expires_at)
    return {"ok": True, "uuid": uid}

import base64
@app.get("/sub/{uid}")
async def render_sub(uid: str, request: Request):
    if uid not in LINKS:
        return PlainTextResponse("Config Not Found", status_code=404)
    link = LINKS[uid]
    if not is_link_allowed(link):
        return PlainTextResponse("Config Expired or Limit Reached", status_code=403)
    host = request.headers.get("host", CONFIG["host"])
    links = get_all_links_for_uuid(link, uid, host)
    raw_text = "\n".join(links)
    encoded = base64.b64encode(raw_text.encode('utf-8')).decode('utf-8')
    return PlainTextResponse(encoded)

@app.websocket("/ws/{uuid}")
async def vless_ws(websocket: WebSocket, uuid: str):
    await _handle_ws_tunnel(websocket, uuid, "vless")

@app.websocket("/trojan-ws/{uuid}")
async def trojan_ws(websocket: WebSocket, uuid: str):
    await _handle_ws_tunnel(websocket, uuid, "trojan")

@app.websocket("/vmess-ws/{uuid}")
async def vmess_ws(websocket: WebSocket, uuid: str):
    await _handle_ws_tunnel(websocket, uuid, "vmess")

async def _handle_ws_tunnel(websocket: WebSocket, uuid: str, protocol: str):
    await websocket.accept()
    link = LINKS.get(uuid)
    client_ip = websocket.client.host if websocket.client else "unknown"

    if not is_link_allowed(link) or not is_ip_allowed(link, uuid, client_ip):
        await websocket.close(code=1008)
        return

    conn_id = f"ws-{id(websocket)}"
    connections[conn_id] = {
        "uuid": uuid, "ip": client_ip,
        "connected_at": datetime.now().isoformat(),
        "bytes": 0, "transport": f"{protocol}-ws"
    }

    writer = None
    try:
        first_packet = await websocket.receive_bytes()
        
        if protocol == "vless":
            cmd, addr, port, payload = await parse_vless_header(first_packet)
        elif protocol == "trojan":
            cmd, addr, port, payload = await parse_trojan_header(first_packet, uuid)
        else:
            cmd, addr, port, payload = 1, "1.1.1.1", 443, first_packet
            
        reader, writer = await asyncio.open_connection(addr, port)
        if payload:
            writer.write(payload)
            await writer.drain()

        async def ws_to_tcp():
            try:
                while True:
                    data = await websocket.receive_bytes()
                    if not data: break
                    if not await check_and_use(uuid, len(data)): break
                    await throttle(uuid, len(data))
                    connections[conn_id]["bytes"] += len(data)
                    writer.write(data)
                    await writer.drain()
            except Exception: pass
            finally: writer.close()

        async def tcp_to_ws():
            try:
                while True:
                    data = await reader.read(16384)
                    if not data: break
                    if not await check_and_use(uuid, len(data)): break
                    await throttle(uuid, len(data))
                    connections[conn_id]["bytes"] += len(data)
                    await websocket.send_bytes(data)
            except Exception: pass
            finally: await websocket.close()

        await asyncio.gather(ws_to_tcp(), tcp_to_ws())
    except WebSocketDisconnect:
        pass
    except Exception as e:
        error_logs.append({"error": f"WS {protocol.upper()} Error: {str(e)}", "time": datetime.now().isoformat()})
    finally:
        if writer:
            try: writer.close()
            except: pass
        connections.pop(conn_id, None)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=CONFIG["port"], loop="uvloop")
