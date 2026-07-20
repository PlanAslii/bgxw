# state.py
import asyncio
import json
import os
import hashlib
import secrets
import time
import tempfile
import aiofiles
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import deque, defaultdict
from pathlib import Path
from urllib.parse import quote
import logging
from fastapi import Request

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("X4G-Core")

IRAN_TZ = ZoneInfo("Asia/Tehran")

env_data = os.environ.get("DATA_DIR")
if env_data:
    DATA_DIR = Path(env_data)
else:
    _local_data = Path("./data")
    try:
        _local_data.mkdir(parents=True, exist_ok=True)
        _test_file = _local_data / ".write_test"
        _test_file.touch()
        _test_file.unlink()
        DATA_DIR = _local_data
    except (OSError, PermissionError):
        logger.warning("Directory './data' is not writable. Falling back to temporary directory.")
        DATA_DIR = Path(tempfile.gettempdir()) / "x4g_data"
        DATA_DIR.mkdir(parents=True, exist_ok=True)

DATA_FILE = DATA_DIR / "x4g_state.json"
SECRET_FILE = DATA_DIR / "x4g_secret.key"
SAVE_LOCK = asyncio.Lock()

def _load_or_create_secret() -> str:
    env_secret = os.environ.get("SECRET_KEY")
    if env_secret: return env_secret
    try:
        if SECRET_FILE.exists():
            existing = SECRET_FILE.read_text(encoding="utf-8").strip()
            if existing: return existing
        new_secret = secrets.token_urlsafe(32)
        SECRET_FILE.write_text(new_secret, encoding="utf-8")
        return new_secret
    except Exception:
        return secrets.token_urlsafe(32)

CONFIG = {
    "port": int(os.environ.get("PORT", 8000)),
    "secret": _load_or_create_secret(),
    "host": os.environ.get("RAILWAY_PUBLIC_DOMAIN", "localhost"),
}

connections: dict = {}
stats = {
    "total_bytes": 0,
    "total_requests": 0,
    "total_errors": 0,
    "start_time": time.time(),
}
error_logs: deque = deque(maxlen=100)
activity_logs: deque = deque(maxlen=200)

LINKS: dict = {}
LINKS_LOCK = asyncio.Lock()
SUBS: dict = {}
SUBS_LOCK = asyncio.Lock()

# پروتکل‌های پشتیبانی شده برای جنریت شدن
SUPPORTED_TRANSPORTS = ("vless-ws", "vless-xhttp", "trojan-ws", "trojan-xhttp", "shadowsocks")
FINGERPRINTS = ("chrome", "firefox", "safari", "ios", "android", "edge", "random")
DEFAULT_FINGERPRINT = "chrome"
DEFAULT_PORT = 443
SS_PORT = int(os.environ.get("SS_PORT", 8388)) # پورت اختصاصی شادوساکس

def get_system_stats():
    """دریافت وضعیت زنده منابع سرور برای نمایش در داشبورد"""
    stats = {"cpu": 0, "ram": 0, "ram_total": 0, "disk": 0}
    if PSUTIL_AVAILABLE:
        stats["cpu"] = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        stats["ram"] = ram.percent
        stats["ram_total"] = ram.total
        disk = psutil.disk_usage('/')
        stats["disk"] = disk.percent
    else:
        # Fallback برای سیستم‌های لینوکسی بدون psutil
        try:
            stats["cpu"] = round(os.getloadavg()[0] / os.cpu_count() * 100, 1)
        except: pass
    return stats
def parse_size_to_bytes(value: float, unit: str) -> int:
    unit = unit.upper()
    if unit == "GB": return int(value * 1024 ** 3)
    if unit == "MB": return int(value * 1024 ** 2)
    if unit == "KB": return int(value * 1024)
    return int(value)

def is_link_expired(link: dict) -> bool:
    exp = link.get("expires_at")
    if not exp: return False
    try:
        return datetime.now() > datetime.fromisoformat(exp)
    except Exception:
        return False

def is_link_allowed(link: dict | None) -> bool:
    if link is None: return False
    if not link.get("active", True): return False
    if is_link_expired(link): return False
    lb = link.get("limit_bytes", 0)
    if lb > 0 and link.get("used_bytes", 0) >= lb: return False
    return True

def fmt_bytes(b: int) -> str:
    if b < 1024: return f"{b} B"
    if b < 1024**2: return f"{b/1024:.1f} KB"
    if b < 1024**3: return f"{b/1024**2:.2f} MB"
    return f"{b/1024**3:.2f} GB"

def unique_ips_for_uuid(uuid: str) -> set:
    return {c.get("ip") for c in connections.values() if c.get("uuid") == uuid and c.get("ip")}

def is_ip_allowed(link: dict | None, uuid: str, ip: str) -> bool:
    if link is None: return False
    limit = int(link.get("ip_limit", 0) or 0)
    if limit <= 0: return True
    ips = unique_ips_for_uuid(uuid)
    if ip in ips: return True
    return len(ips) < limit

def get_host(request: Request | None = None) -> str:
    if request is not None:
        h = request.headers.get("x-forwarded-host") or request.headers.get("host")
        if h:
            h = h.split(":")[0]
            CONFIG["host"] = h
            return h
    return os.environ.get("RAILWAY_PUBLIC_DOMAIN", CONFIG["host"])

def generate_uuid() -> str:
    h = secrets.token_hex(16)
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"

def generate_protocol_link(
    protocol_type: str,
    uuid: str,
    host: str,
    remark: str,
    fingerprint: str = DEFAULT_FINGERPRINT,
    port: int = DEFAULT_PORT
) -> str:
    """تولید کانفیگ متناسب با نوع پروتکل"""
    fp = fingerprint if fingerprint in FINGERPRINTS else DEFAULT_FINGERPRINT
    
    if protocol_type == "shadowsocks":
        import base64
        # روش استاندارد شادوساکس AEAD
        method = "chacha20-ietf-poly1305"
        # در شادوساکس رمز عبور همان UUID کاربر است
        credentials = f"{method}:{uuid}"
        encoded_creds = base64.urlsafe_b64encode(credentials.encode()).decode().rstrip("=")
        # توجه: پورت شادوساکس مجزا از پورت وب است
        return f"ss://{encoded_creds}@{host}:{SS_PORT}#{quote(remark + ' [SS-AEAD]')}"
        
    elif protocol_type == "vless-ws":
        params = {"encryption": "none", "security": "tls", "type": "ws", "host": host, "path": f"/ws/{uuid}", "sni": host, "fp": fp, "alpn": "http/1.1"}
        query = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
        return f"vless://{uuid}@{host}:{port}?{query}#{quote(remark + ' [VLESS-WS]')}"
        
    elif protocol_type == "vless-xhttp":
        params = {"encryption": "none", "security": "tls", "type": "xhttp", "mode": "packet-up", "host": host, "path": f"/xhttp-siz10/packet-up/{uuid}", "sni": host, "fp": fp, "alpn": "h2,http/1.1"}
        query = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
        return f"vless://{uuid}@{host}:{port}?{query}#{quote(remark + ' [VLESS-xHTTP]')}"
        
    elif protocol_type == "trojan-ws":
        # برای تروجان از همان UUID به عنوان پسورد استفاده میکنیم
        params = {"security": "tls", "type": "ws", "host": host, "path": f"/trojan-ws/{uuid}", "sni": host, "fp": fp, "alpn": "http/1.1"}
        query = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
        return f"trojan://{uuid}@{host}:{port}?{query}#{quote(remark + ' [Trojan-WS]')}"
        
    elif protocol_type == "trojan-xhttp":
        params = {"security": "tls", "type": "xhttp", "mode": "packet-up", "host": host, "path": f"/xhttp-trojan/packet-up/{uuid}", "sni": host, "fp": fp, "alpn": "h2,http/1.1"}
        query = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
        return f"trojan://{uuid}@{host}:{port}?{query}#{quote(remark + ' [Trojan-xHTTP]')}"
        
    return ""

def get_all_links_for_uuid(link: dict, uid: str, host: str) -> list:
    remark = f"X4G-{link.get('label', '')}"
    fp = link.get("fingerprint", DEFAULT_FINGERPRINT)
    port = link.get("port", DEFAULT_PORT)
    
    return [
        generate_protocol_link("vless-ws", uid, host, remark, fp, port),
        generate_protocol_link("vless-xhttp", uid, host, remark, fp, port),
        generate_protocol_link("trojan-ws", uid, host, remark, fp, port),
        generate_protocol_link("trojan-xhttp", uid, host, remark, fp, port),
        generate_protocol_link("shadowsocks", uid, host, remark, fp, SS_PORT)
    ]

async def load_state():
    try:
        if DATA_FILE.exists():
            async with aiofiles.open(DATA_FILE, "r", encoding="utf-8") as f:
                raw = await f.read()
            data = json.loads(raw)
            LINKS.update(data.get("links", {}))
            SUBS.update(data.get("subs", {}))
            if "password_hash" in data:
                AUTH["password_hash"] = data["password_hash"]
            logger.info(f"State loaded: {len(LINKS)} links, {len(SUBS)} subs")
    except Exception as e:
        logger.warning(f"Could not load state: {e}")

async def save_state():
    async with SAVE_LOCK:
        try:
            data = {
                "links": dict(LINKS),
                "subs": dict(SUBS),
                "password_hash": AUTH["password_hash"],
                "saved_at": datetime.now().isoformat(),
            }
            tmp = DATA_FILE.with_suffix(".tmp")
            async with aiofiles.open(tmp, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            tmp.replace(DATA_FILE)
        except Exception as e:
            logger.warning(f"Could not save state: {e}")

async def make_link(
    label: str = "لینک جدید",
    limit_bytes: int = 0,
    expires_at: str | None = None,
    note: str = "",
    sub_id: str | None = None,
    fingerprint: str = DEFAULT_FINGERPRINT,
    port: int = DEFAULT_PORT,
    ip_limit: int = 0,
    speed_limit_bytes: int = 0,
) -> tuple[str, dict]:
    uid = generate_uuid()
    async with LINKS_LOCK:
        LINKS[uid] = {
            "label": (label or "لینک جدید").strip()[:60] or "لینک جدید",
            "limit_bytes": max(0, limit_bytes),
            "used_bytes": 0,
            "created_at": datetime.now().isoformat(),
            "active": True,
            "expires_at": expires_at,
            "note": (note or "").strip()[:200],
            "sub_id": sub_id,
            "fingerprint": fingerprint,
            "port": port,
            "ip_limit": max(0, ip_limit),
            "speed_limit_bytes": max(0, speed_limit_bytes),
        }
    if sub_id:
        async with SUBS_LOCK:
            if sub_id in SUBS:
                ids = SUBS[sub_id].setdefault("link_ids", [])
                if uid not in ids:
                    ids.append(uid)
    asyncio.create_task(save_state())
    log_activity("link", f"مولتی کانفیگ «{LINKS[uid]['label']}» ساخته شد", "ok")
    return uid, LINKS[uid]

async def create_multipack(label: str, limit_bytes: int, expires_days: int) -> tuple[str, str]:
    """ساخت یک گروه ساب جدید و اختصاص یک کانفیگ مولتی پروتکل به آن"""
    # 1. ساخت گروه
    sub_id = generate_uuid()
    uuid_key = secrets.token_urlsafe(16)
    async with SUBS_LOCK:
        SUBS[sub_id] = {
            "name": f"گروه پک {label}",
            "desc": "ساخته شده توسط مولتی پک",
            "password_hash": None,
            "uuid_key": uuid_key,
            "created_at": datetime.now().isoformat(),
            "link_ids": [],
        }
    
    # 2. ساخت لینک و افزودن به گروه
    expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat() if expires_days > 0 else None
    await make_link(
        label=label,
        limit_bytes=limit_bytes,
        expires_at=expires_at,
        sub_id=sub_id
    )
    
    return sub_id, uuid_key

async def remove_link(uid: str) -> str | None:
    async with LINKS_LOCK:
        if uid not in LINKS: return None
        label = LINKS[uid].get("label", uid)
        sub_id = LINKS[uid].get("sub_id")
        del LINKS[uid]
    if sub_id:
        async with SUBS_LOCK:
            if sub_id in SUBS:
                ids = SUBS[sub_id].get("link_ids", [])
                if uid in ids: ids.remove(uid)
    asyncio.create_task(save_state())
    log_activity("link", f"کانفیگ «{label}» حذف شد", "err")
    return label

async def remove_sub_group(sub_id: str) -> str | None:
    async with SUBS_LOCK:
        if sub_id not in SUBS: return None
        name = SUBS[sub_id].get("name", sub_id)
        del SUBS[sub_id]
    async with LINKS_LOCK:
        for link in LINKS.values():
            if link.get("sub_id") == sub_id:
                link["sub_id"] = None
    asyncio.create_task(save_state())
    log_activity("sub", f"گروه «{name}» حذف شد", "warn")
    return name
