# main.py
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from contextlib import asynccontextmanager
from datetime import datetime
import hashlib
import secrets

from state import (
    load_state, save_state, CONFIG, logger, AUTH, DEFAULT_PASSWORD,
    LINKS, is_link_allowed, is_ip_allowed, connections, error_logs,
    get_all_links_for_uuid, make_link, remove_link, update_link,
    log_activity
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

security = HTTPBasic()

def verify_auth(credentials: HTTPBasicCredentials = Depends(security)):
    """بررسی احراز هویت برای مسیرهای مدیریتی"""
    password_hash = hashlib.sha256(credentials.password.encode()).hexdigest()
    if AUTH["password_hash"] != password_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return True

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting OXNet Core Server (Multi-Protocol Edition)...")
    await load_state()
    
    # نمایش رمز پیش‌فرض در صورت عدم تغییر
    if not AUTH.get("password_changed", False):
        logger.info(f"Default password: {DEFAULT_PASSWORD}")
        print(f"\n⚠️  Default password: {DEFAULT_PASSWORD}\n")
    
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

@app.post("/api/auth/login")
async def login(request: Request):
    """ورود به پنل و دریافت توکن"""
    data = await request.json()
    password = data.get("password", "")
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if AUTH["password_hash"] != password_hash:
        return JSONResponse({"ok": False, "error": "رمز عبور اشتباه است"}, status_code=401)
    
    # تولید توکن ساده (برای دمو)
    token = secrets.token_urlsafe(32)
    return {"ok": True, "token": token}

@app.post("/api/auth/change-password")
async def change_password(request: Request, auth: bool = Depends(verify_auth)):
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
    """دریافت رمز پیش‌فرض پنل"""
    return {"default_password": DEFAULT_PASSWORD if not AUTH.get("password_changed", False) else None}

@app.get("/api/panel/stats")
async def get_stats(auth: bool = Depends(verify_auth)):
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
async def get_links(auth: bool = Depends(verify_auth)):
    return {"links": LINKS}

@app.get("/api/panel/links/{uid}")
async def get_link(uid: str, auth: bool = Depends(verify_auth)):
    if uid not in LINKS:
        return JSONResponse({"error": "لینک یافت نشد"}, status_code=404)
    return {"link": LINKS[uid]}

@app.put("/api/panel/links/{uid}")
async def edit_link(uid: str, request: Request, auth: bool = Depends(verify_auth)):
    """ویرایش لینک"""
    if uid not in LINKS:
        return JSONResponse({"error": "لینک یافت نشد"}, status_code=404)
    
    data = await request.json()
    updated = await update_link(uid, data)
    if not updated:
        return JSONResponse({"error": "خطا در ویرایش"}, status_code=400)
    
    return {"ok": True, "link": updated}

@app.delete("/api/panel/links/{uid}")
async def del_link(uid: str, auth: bool = Depends(verify_auth)):
    res = await remove_link(uid)
    return {"ok": res is not None}

@app.post("/api/panel/multipack")
async def api_create_multipack(request: Request, auth: bool = Depends(verify_auth)):
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
    
    # Base64 encode for standard subscription format
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

# هسته مرکزی تونل زنی وب سوکت مشترک
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
        else:  # vmess
            # برای VMESS باید هدر جداگانه پیاده‌سازی شود
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
