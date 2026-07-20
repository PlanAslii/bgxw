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
logger = logging.getLogger("OXNet-Core")

IRAN_TZ = ZoneInfo("Asia/Tehran")

# ========== DIRECTORY SETUP ==========
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
        DATA_DIR = Path(tempfile.gettempdir()) / "oxnet_data"
        DATA_DIR.mkdir(parents=True, exist_ok=True)

DATA_FILE = DATA_DIR / "oxnet_state.json"
SECRET_FILE = DATA_DIR / "oxnet_secret.key"
SAVE_LOCK = asyncio.Lock()

logger.info(f"Data directory: {DATA_DIR}")
logger.info(f"Data file: {DATA_FILE}")

# ========== AUTH ==========
AUTH = {
    "password_hash": "",
    "password_changed": False
}

def is_first_run() -> bool:
    """بررسی اینکه آیا رمز عبور تنظیم شده است یا خیر"""
    return not AUTH.get("password_hash") or AUTH["password_hash"] == ""

async def set_first_run_password(password: str) -> bool:
    """تنظیم رمز عبور برای اولین بار"""
    if not password or len(password) < 6:
        return False
    
    AUTH["password_hash"] = hashlib.sha256(password.encode()).hexdigest()
    AUTH["password_changed"] = True
    
    # ذخیره فوری
    await save_state()
    
    logger.info("✅ Password set successfully!")
    return True

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

# پروتکل‌های پشتیبانی شده
SUPPORTED_TRANSPORTS = (
    "vless-ws", "vless-xhttp", "vless-grpc", "vless-quic",
    "trojan-ws", "trojan-xhttp", "trojan-grpc",
    "vmess-ws", "vmess-xhttp", "vmess-grpc",
    "shadowsocks", "shadowsocks-xhttp",
    "mtproto"
)
FINGERPRINTS = ("chrome", "firefox", "safari", "ios", "android", "edge", "random", "none")
DEFAULT_FINGERPRINT = "chrome"
DEFAULT_PORT = 443
SS_PORT = int(os.environ.get("SS_PORT", 8388))
MTProto_PORT = int(os.environ.get("MTPROTO_PORT", 4433))

def get_system_stats():
    stats = {"cpu": 0, "ram": 0, "ram_total": 0, "disk": 0}
    if PSUTIL_AVAILABLE:
        stats["cpu"] = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        stats["ram"] = ram.percent
        stats["ram_total"] = ram.total
        disk = psutil.disk_usage('/')
        stats["disk"] = disk.percent
    else:
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
    port: int = DEFAULT_PORT,
    extra_params: dict = None
) -> str:
    fp = fingerprint if fingerprint in FINGERPRINTS else DEFAULT_FINGERPRINT
    extra = extra_params or {}
    
    if protocol_type == "shadowsocks":
        import base64
        method = "chacha20-ietf-poly1305"
        credentials = f"{method}:{uuid}"
        encoded_creds = base64.urlsafe_b64encode(credentials.encode()).decode().rstrip("=")
        return f"ss://{encoded_creds}@{host}:{SS_PORT}#{quote(remark + ' [SS-AEAD]')}"
    
    elif protocol_type == "shadowsocks-xhttp":
        import base64
        method = "chacha20-ietf-poly1305"
        credentials = f"{method}:{uuid}"
        encoded_creds = base64.urlsafe_b64encode(credentials.encode()).decode().rstrip("=")
        return f"ss-xhttp://{encoded_creds}@{host}:{port}?path=/xhttp-ss/packet-up/{uuid}#{quote(remark + ' [SS-xHTTP]')}"
        
    elif protocol_type == "vless-ws":
        params = {"encryption": "none", "security": "tls", "type": "ws", "host": host, "path": f"/ws/{uuid}", "sni": host, "fp": fp, "alpn": "http/1.1"}
        query = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
        return f"vless://{uuid}@{host}:{port}?{query}#{quote(remark + ' [VLESS-WS]')}"
        
    elif protocol_type == "vless-xhttp":
        params = {"encryption": "none", "security": "tls", "type": "xhttp", "mode": "packet-up", "host": host, "path": f"/xhttp-siz10/packet-up/{uuid}", "sni": host, "fp": fp, "alpn": "h2,http/1.1"}
        query = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
        return f"vless://{uuid}@{host}:{port}?{query}#{quote(remark + ' [VLESS-xHTTP]')}"
    
    elif protocol_type == "vless-grpc":
        params = {"encryption": "none", "security": "tls", "type": "grpc", "serviceName": f"/grpc/{uuid}", "host": host, "sni": host, "fp": fp, "alpn": "h2"}
        query = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
        return f"vless://{uuid}@{host}:{port}?{query}#{quote(remark + ' [VLESS-gRPC]')}"
    
    elif protocol_type == "vless-quic":
        params = {"encryption": "none", "security": "tls", "type": "quic", "host": host, "sni": host, "fp": fp}
        query = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
        return f"vless://{uuid}@{host}:{port}?{query}#{quote(remark + ' [VLESS-QUIC]')}"
        
    elif protocol_type == "trojan-ws":
        params = {"security": "tls", "type": "ws", "host": host, "path": f"/trojan-ws/{uuid}", "sni": host, "fp": fp, "alpn": "http/1.1"}
        query = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
        return f"trojan://{uuid}@{host}:{port}?{query}#{quote(remark + ' [Trojan-WS]')}"
        
    elif protocol_type == "trojan-xhttp":
        params = {"security": "tls", "type": "xhttp", "mode": "packet-up", "host": host, "path": f"/xhttp-trojan/packet-up/{uuid}", "sni": host, "fp": fp, "alpn": "h2,http/1.1"}
        query = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
        return f"trojan://{uuid}@{host}:{port}?{query}#{quote(remark + ' [Trojan-xHTTP]')}"
    
    elif protocol_type == "trojan-grpc":
        params = {"security": "tls", "type": "grpc", "serviceName": f"/trojan-grpc/{uuid}", "host": host, "sni": host, "fp": fp, "alpn": "h2"}
        query = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
        return f"trojan://{uuid}@{host}:{port}?{query}#{quote(remark + ' [Trojan-gRPC]')}"
        
    elif protocol_type == "vmess-ws":
        import base64
        import json
        vmess_obj = {
            "v": "2", "ps": f"{remark} [VMESS-WS]",
            "add": host, "port": port, "id": uuid,
            "aid": "0", "net": "ws", "type": "none",
            "host": host, "path": f"/vmess-ws/{uuid}",
            "tls": "tls", "sni": host, "fp": fp
        }
        return f"vmess://{base64.b64encode(json.dumps(vmess_obj).encode()).decode()}"
    
    elif protocol_type == "vmess-xhttp":
        import base64
        import json
        vmess_obj = {
            "v": "2", "ps": f"{remark} [VMESS-xHTTP]",
            "add": host, "port": port, "id": uuid,
            "aid": "0", "net": "xhttp", "type": "packet-up",
            "host": host, "path": f"/xhttp-vmess/packet-up/{uuid}",
            "tls": "tls", "sni": host, "fp": fp
        }
        return f"vmess://{base64.b64encode(json.dumps(vmess_obj).encode()).decode()}"
    
    elif protocol_type == "vmess-grpc":
        import base64
        import json
        vmess_obj = {
            "v": "2", "ps": f"{remark} [VMESS-gRPC]",
            "add": host, "port": port, "id": uuid,
            "aid": "0", "net": "grpc", "type": "none",
            "host": host, "path": f"/vmess-grpc/{uuid}",
            "tls": "tls", "sni": host, "fp": fp
        }
        return f"vmess://{base64.b64encode(json.dumps(vmess_obj).encode()).decode()}"
    
    elif protocol_type == "mtproto":
        import base64
        secret = base64.urlsafe_b64encode(uuid.encode()).decode().rstrip("=")
        return f"tg://proxy?server={host}&port={MTProto_PORT}&secret={secret}#{quote(remark + ' [MTProto]')}"
        
    return ""

def get_all_links_for_uuid(link: dict, uid: str, host: str) -> list:
    remark = f"OXNet-{link.get('label', '')}"
    fp = link.get("fingerprint", DEFAULT_FINGERPRINT)
    port = link.get("port", DEFAULT_PORT)
    
    protocols = [
        ("vless-ws", "VLESS-WS"),
        ("vless-xhttp", "VLESS-xHTTP"),
        ("vless-grpc", "VLESS-gRPC"),
        ("trojan-ws", "Trojan-WS"),
        ("trojan-xhttp", "Trojan-xHTTP"),
        ("trojan-grpc", "Trojan-gRPC"),
        ("vmess-ws", "VMESS-WS"),
        ("vmess-xhttp", "VMESS-xHTTP"),
        ("vmess-grpc", "VMESS-gRPC"),
        ("shadowsocks", "SS-AEAD"),
        ("shadowsocks-xhttp", "SS-xHTTP"),
        ("mtproto", "MTProto")
    ]
    
    links = []
    for proto, label in protocols:
        try:
            link_str = generate_protocol_link(proto, uid, host, f"{remark} [{label}]", fp, port)
            if link_str:
                links.append(link_str)
        except Exception as e:
            logger.warning(f"Failed to generate {proto} link: {e}")
    
    return links

async def load_state():
    """بارگذاری وضعیت از فایل"""
    global AUTH, LINKS, SUBS
    try:
        if DATA_FILE.exists():
            async with aiofiles.open(DATA_FILE, "r", encoding="utf-8") as f:
                raw = await f.read()
            data = json.loads(raw)
            
            LINKS.update(data.get("links", {}))
            SUBS.update(data.get("subs", {}))
            
            if "password_hash" in data:
                AUTH["password_hash"] = data["password_hash"]
            if "password_changed" in data:
                AUTH["password_changed"] = data["password_changed"]
            
            logger.info(f"✅ State loaded: {len(LINKS)} links, {len(SUBS)} subs")
            logger.info(f"🔑 Password set: {bool(AUTH['password_hash'])}")
        else:
            logger.warning("⚠️ No state file found. Starting fresh.")
            # ایجاد فایل جدید با وضعیت خالی
            await save_state()
    except Exception as e:
        logger.error(f"❌ Could not load state: {e}")
        # ایجاد فایل جدید در صورت خطا
        await save_state()

async def save_state():
    """ذخیره وضعیت در فایل"""
    async with SAVE_LOCK:
        try:
            data = {
                "links": dict(LINKS),
                "subs": dict(SUBS),
                "password_hash": AUTH["password_hash"],
                "password_changed": AUTH["password_changed"],
                "saved_at": datetime.now().isoformat(),
            }
            
            # اطمینان از وجود دایرکتوری
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            
            # نوشتن در فایل موقت و سپس جایگزینی
            tmp = DATA_FILE.with_suffix(".tmp")
            async with aiofiles.open(tmp, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            tmp.replace(DATA_FILE)
            
            logger.debug(f"💾 State saved: {len(LINKS)} links")
            return True
        except Exception as e:
            logger.error(f"❌ Could not save state: {e}")
            return False

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
            "edited_at": datetime.now().isoformat(),
        }
    if sub_id:
        async with SUBS_LOCK:
            if sub_id in SUBS:
                ids = SUBS[sub_id].setdefault("link_ids", [])
                if uid not in ids:
                    ids.append(uid)
    await save_state()
    log_activity("link", f"مولتی کانفیگ «{LINKS[uid]['label']}» ساخته شد", "ok")
    return uid, LINKS[uid]

async def update_link(uid: str, updates: dict) -> dict | None:
    async with LINKS_LOCK:
        if uid not in LINKS:
            return None
        link = LINKS[uid]
        
        editable_fields = [
            "label", "limit_bytes", "expires_at", "note", 
            "fingerprint", "port", "ip_limit", "speed_limit_bytes", "active"
        ]
        
        for field in editable_fields:
            if field in updates and updates[field] is not None:
                if field == "limit_bytes":
                    link[field] = max(0, int(updates[field]))
                elif field in ["ip_limit", "port", "speed_limit_bytes"]:
                    link[field] = max(0, int(updates[field]))
                elif field == "active":
                    link[field] = bool(updates[field])
                else:
                    link[field] = updates[field]
        
        link["edited_at"] = datetime.now().isoformat()
        
    await save_state()
    log_activity("link", f"کانفیگ «{link['label']}» ویرایش شد", "ok")
    return link

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
    await save_state()
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
    await save_state()
    log_activity("sub", f"گروه «{name}» حذف شد", "warn")
    return name

def log_activity(category: str, message: str, level: str = "info"):
    activity_logs.append({
        "time": datetime.now().isoformat(),
        "category": category,
        "message": message,
        "level": level
    })
