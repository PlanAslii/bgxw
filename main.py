# main.py
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime

from state import (
    load_state, save_state, CONFIG, logger,
    LINKS, is_link_allowed, is_ip_allowed, connections, error_logs,
    get_all_links_for_uuid, make_link, remove_link
)
from xhttp_siz10 import router as xhttp_router
from relay_protocols import parse_vless_header, parse_trojan_header, check_and_use
from speed_limit import throttle
from pages import DASHBOARD_HTML

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting X4G Core Server (Dark Multi-Protocol Edition)...")
    await load_state()
    yield
    logger.info("Shutting down X4G Core...")
    await save_state()

app = FastAPI(title="X4G Xray Backend", lifespan=lifespan)
app.include_router(xhttp_router)

@app.get("/")
async def root():
    return HTMLResponse(DASHBOARD_HTML)

@app.get("/api/panel/stats")
async def get_stats():
    total_vol = sum(l.get("used_bytes", 0) for l in LINKS.values())
    return {
        "total_links": len(LINKS),
        "total_traffic_bytes": total_vol,
        "online_users": len(connections)
    }

@app.get("/api/panel/links")
async def get_links():
    return {"links": LINKS}

@app.delete("/api/panel/links/{uid}")
async def del_link(uid: str):
    res = await remove_link(uid)
    return {"ok": res is not None}

@app.post("/api/panel/multipack")
async def api_create_multipack(request: Request):
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
        else: # trojan
            cmd, addr, port, payload = await parse_trojan_header(first_packet, uuid)
            
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
