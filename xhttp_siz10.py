# xhttp_siz10.py
import asyncio
import secrets
import socket
import time
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse

from state import (
    LINKS, LINKS_LOCK, stats, connections, error_logs, logger,
    is_link_allowed, is_ip_allowed, save_state
)
from relay_protocols import (
    parse_vless_header, parse_trojan_header, parse_vmess_header, 
    parse_shadowsocks_header, check_and_use
)
from speed_limit import throttle

router = APIRouter()

XHTTP_BUF = 512 * 1024
DOWNLINK_QUEUE_MAX = 512
SESSION_IDLE_TIMEOUT = 30
REAPER_INTERVAL = 10
TCP_CONNECT_TIMEOUT = 10.0
SOCK_BUF_SIZE = 2 * 1024 * 1024     

xhttp_sessions: dict = {}
XHTTP_LOCK = asyncio.Lock()

def _resp_headers() -> dict:
    return {
        "content-type": "application/grpc",
        "cache-control": "no-cache, no-store",
        "x-accel-buffering": "no",
        "server": "cloudflare",
    }

def _tune_socket(writer: asyncio.StreamWriter):
    sock = writer.transport.get_extra_info("socket")
    if not sock: return
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SOCK_BUF_SIZE)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCK_BUF_SIZE)
    except OSError: pass

class _QuotaGate:
    __slots__ = ("uuid", "pending", "ok")
    def __init__(self, uuid: str):
        self.uuid = uuid
        self.pending = 0
        self.ok = True

    async def add(self, nbytes: int) -> bool:
        if not self.ok: return False
        self.pending += nbytes
        if self.pending >= 64 * 1024:
            flush, self.pending = self.pending, 0
            self.ok = await check_and_use(self.uuid, flush)
        return self.ok

    async def flush(self) -> bool:
        if self.pending:
            flush, self.pending = self.pending, 0
            self.ok = self.ok and await check_and_use(self.uuid, flush)
        return self.ok

async def _open_tcp_tunnel(first_chunk: bytes, protocol: str, uuid: str):
    if protocol == "vless":
        cmd, address, port, payload = await parse_vless_header(first_chunk)
    elif protocol == "trojan":
        cmd, address, port, payload = await parse_trojan_header(first_chunk, uuid)
    elif protocol == "vmess":
        cmd, address, port, payload = await parse_vmess_header(first_chunk, uuid)
    elif protocol == "shadowsocks":
        cmd, address, port, payload = await parse_shadowsocks_header(first_chunk)
    else:
        raise ValueError(f"Unknown protocol: {protocol}")

    reader, writer = await asyncio.wait_for(
        asyncio.open_connection(address, port), timeout=TCP_CONNECT_TIMEOUT
    )
    _tune_socket(writer)
    if payload:
        writer.write(payload)
        await writer.drain()
    return reader, writer, address, port

async def _get_or_create_session(uuid: str, mode: str, session_id: str, ip: str, protocol: str) -> dict:
    async with XHTTP_LOCK:
        sess = xhttp_sessions.get(session_id)
        if sess is not None:
            sess["last_seen"] = time.time()
            return sess

        async with LINKS_LOCK:
            link = LINKS.get(uuid)
        if not is_ip_allowed(link, uuid, ip):
            raise HTTPException(status_code=403, detail="ip limit reached")

        conn_id = secrets.token_urlsafe(6)
        connections[conn_id] = {
            "uuid": uuid,
            "ip": ip,
            "connected_at": datetime.now().isoformat(),
            "bytes": 0,
            "transport": f"xhttp-{protocol}",
        }
        sess = {
            "uuid": uuid, "mode": mode, "protocol": protocol,
            "writer": None, "downlink_task": None,
            "down_q": asyncio.Queue(maxsize=DOWNLINK_QUEUE_MAX),
            "last_seen": time.time(),
            "conn_id": conn_id, "tcp_open": False, "closed": False,
            "seq_buf": {}, "next_seq": 0,
        }
        xhttp_sessions[session_id] = sess
        return sess

async def _teardown(session_id: str):
    async with XHTTP_LOCK:
        sess = xhttp_sessions.pop(session_id, None)
    if not sess: return
    sess["closed"] = True
    if sess.get("downlink_task"):
        sess["downlink_task"].cancel()
    writer = sess.get("writer")
    if writer:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception: pass
    connections.pop(sess.get("conn_id"), None)
    dq = sess.get("down_q")
    if dq:
        try: dq.put_nowait(None)
        except Exception: pass

async def _pump_tcp_to_queue(session_id: str, uuid: str, reader: asyncio.StreamReader, down_q: asyncio.Queue):
    first = True
    gate = _QuotaGate(uuid)  
    try:
        while True:
            data = await reader.read(XHTTP_BUF)
            if not data: break
            if not await gate.add(len(data)): break
            await throttle(uuid, len(data))
            
            async with XHTTP_LOCK:
                sess = xhttp_sessions.get(session_id)
            if sess and sess["conn_id"] in connections:
                connections[sess["conn_id"]]["bytes"] += len(data)
                
            payload = (b"\x00\x00" + data) if first else data
            first = False
            await down_q.put(payload)
    except Exception: pass
    finally:
        await gate.flush()
        await _teardown(session_id)

def _downstream_gen(sess: dict):
    async def gen():
        try:
            while True:
                chunk = await sess["down_q"].get()
                if chunk is None: break
                sess["last_seen"] = time.time()
                yield chunk
        finally: pass
    return gen()

@router.get("/xhttp-siz10/{mode}/{uuid}/{session_id}")
@router.get("/xhttp-trojan/{mode}/{uuid}/{session_id}")
@router.get("/xhttp-vmess/{mode}/{uuid}/{session_id}")
@router.get("/xhttp-ss/{mode}/{uuid}/{session_id}")
async def xhttp_downlink(mode: str, uuid: str, session_id: str, request: Request):
    path = request.url.path
    if "trojan" in path:
        protocol = "trojan"
    elif "vmess" in path:
        protocol = "vmess"
    elif "ss" in path:
        protocol = "shadowsocks"
    else:
        protocol = "vless"
    
    async with LINKS_LOCK:
        link = LINKS.get(uuid)
    if not is_link_allowed(link):
        raise HTTPException(status_code=403, detail="not authorized")
        
    ip = request.client.host if request.client else "unknown"
    sess = await _get_or_create_session(uuid, mode, session_id, ip, protocol)
    if sess.get("closed"): raise HTTPException(status_code=404, detail="session closed")

    headers = _resp_headers()
    return StreamingResponse(_downstream_gen(sess), headers=headers, media_type=headers["content-type"])

@router.post("/xhttp-siz10/packet-up/{uuid}/{session_id}/{seq}")
@router.post("/xhttp-trojan/packet-up/{uuid}/{session_id}/{seq}")
@router.post("/xhttp-vmess/packet-up/{uuid}/{session_id}/{seq}")
@router.post("/xhttp-ss/packet-up/{uuid}/{session_id}/{seq}")
async def packet_up_upload(uuid: str, session_id: str, seq: int, request: Request):
    path = request.url.path
    if "trojan" in path:
        protocol = "trojan"
    elif "vmess" in path:
        protocol = "vmess"
    elif "ss" in path:
        protocol = "shadowsocks"
    else:
        protocol = "vless"
        
    ip = request.client.host if request.client else "unknown"
    
    sess = await _get_or_create_session(uuid, "packet-up", session_id, ip, protocol)
    if sess.get("closed"): raise HTTPException(status_code=404, detail="session closed")

    sess["last_seen"] = time.time()
    body = await request.body()
    if not body: return {"ok": True}

    if not await check_and_use(uuid, len(body)):
        await _teardown(session_id)
        raise HTTPException(status_code=403, detail="quota exhausted")
    await throttle(uuid, len(body))

    stats["total_requests"] += 1
    if sess["conn_id"] in connections:
        connections[sess["conn_id"]]["bytes"] += len(body)

    try:
        if sess["writer"] is None:
            if seq != 0:
                sess["seq_buf"][seq] = body
                return {"ok": True, "buffered": True}
                
            reader, writer, addr, port = await _open_tcp_tunnel(body, protocol, uuid)
            sess["writer"] = writer
            sess["tcp_open"] = True
            sess["downlink_task"] = asyncio.create_task(_pump_tcp_to_queue(session_id, uuid, reader, sess["down_q"]))
            
            nxt = 1
            while nxt in sess["seq_buf"]:
                sess["writer"].write(sess["seq_buf"].pop(nxt))
                nxt += 1
            sess["next_seq"] = nxt
            return {"ok": True, "connected": True}

        if seq == sess["next_seq"]:
            sess["writer"].write(body)
            sess["next_seq"] += 1
            while sess["next_seq"] in sess["seq_buf"]:
                sess["writer"].write(sess["seq_buf"].pop(sess["next_seq"]))
                sess["next_seq"] += 1
        else:
            sess["seq_buf"][seq] = body

        await sess["writer"].drain()
    except Exception as exc:
        await _teardown(session_id)
        raise HTTPException(status_code=502, detail="write failed")

    return {"ok": True}

@router.post("/grpc/{uuid}/{session_id}")
async def grpc_tunnel(uuid: str, session_id: str, request: Request):
    protocol = request.headers.get("x-protocol", "vless")
    ip = request.client.host if request.client else "unknown"
    
    async with LINKS_LOCK:
        link = LINKS.get(uuid)
    if not is_link_allowed(link):
        raise HTTPException(status_code=403, detail="not authorized")
    if not is_ip_allowed(link, uuid, ip):
        raise HTTPException(status_code=403, detail="ip limit reached")
    
    body = await request.body()
    if not body:
        return {"ok": True}
    
    try:
        if protocol == "vless":
            cmd, addr, port, payload = await parse_vless_header(body)
        elif protocol == "trojan":
            cmd, addr, port, payload = await parse_trojan_header(body, uuid)
        elif protocol == "vmess":
            cmd, addr, port, payload = await parse_vmess_header(body, uuid)
        else:
            return {"ok": False, "error": "Unsupported protocol"}
        
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(addr, port), timeout=TCP_CONNECT_TIMEOUT
        )
        _tune_socket(writer)
        
        if payload:
            writer.write(payload)
            await writer.drain()
        
        response = await reader.read(8192)
        writer.close()
        await writer.wait_closed()
        
        return {"ok": True, "data": response.hex() if response else ""}
        
    except Exception as e:
        logger.error(f"gRPC error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
