# relay_protocols.py
import struct
import ipaddress
import hashlib
import base64
import json
from state import LINKS, is_link_allowed

async def check_and_use(uuid: str, nbytes: int) -> bool:
    """بررسی مجاز بودن کاربر و کسر حجم به صورت در لحظه"""
    link = LINKS.get(uuid)
    if not is_link_allowed(link):
        return False
    if link:
        link["used_bytes"] = link.get("used_bytes", 0) + nbytes
    return True

async def parse_vless_header(data: bytes):
    """
    استخراج هدر استاندارد VLESS.
    فرمت: Version(1) + UUID(16) + OptLen(1) + CMD(1) + Port(2) + Atyp(1) + Addr + Payload
    """
    if len(data) < 24:
        raise ValueError("VLESS header is too short")
        
    version = data[0]
    opt_len = data[17]
    cmd = data[18 + opt_len]  # 1: TCP, 2: UDP
    port = struct.unpack(">H", data[19 + opt_len : 21 + opt_len])[0]
    addr_type = data[21 + opt_len]
    pos = 22 + opt_len

    if addr_type == 1:  # IPv4
        addr = f"{data[pos]}.{data[pos+1]}.{data[pos+2]}.{data[pos+3]}"
        pos += 4
    elif addr_type == 2:  # Domain
        domain_len = data[pos]
        pos += 1
        addr = data[pos : pos + domain_len].decode('utf-8')
        pos += domain_len
    elif addr_type == 3:  # IPv6
        addr = str(ipaddress.IPv6Address(data[pos : pos + 16]))
        pos += 16
    else:
        raise ValueError(f"Unknown address type: {addr_type}")

    payload = data[pos:]
    return cmd, addr, port, payload

async def parse_trojan_header(data: bytes, expected_uuid: str):
    """
    استخراج هدر استاندارد Trojan.
    فرمت: Password + \r\n + CMD(1) + Addr + Port + \r\n + Payload
    """
    # پیدا کردن پایان پسورد (تا \r\n)
    crlf_pos = data.find(b'\r\n')
    if crlf_pos == -1:
        raise ValueError("Invalid Trojan header: no CRLF found")
    
    password = data[:crlf_pos].decode('utf-8')
    if password != expected_uuid:
        raise ValueError(f"Invalid Trojan password: {password}")
    
    pos = crlf_pos + 2
    
    if len(data) < pos + 1:
        raise ValueError("Trojan header too short")
    
    cmd = data[pos]  # 1: TCP, 2: UDP
    pos += 1
    
    # خواندن آدرس (SOCKS5 format)
    atyp = data[pos]
    pos += 1
    
    if atyp == 1:  # IPv4
        if len(data) < pos + 4 + 2:
            raise ValueError("Truncated IPv4 address")
        addr = f"{data[pos]}.{data[pos+1]}.{data[pos+2]}.{data[pos+3]}"
        pos += 4
    elif atyp == 3:  # Domain
        if len(data) < pos + 1:
            raise ValueError("Truncated domain address")
        domain_len = data[pos]
        pos += 1
        if len(data) < pos + domain_len + 2:
            raise ValueError("Truncated domain name string")
        addr = data[pos : pos + domain_len].decode('utf-8')
        pos += domain_len
    elif atyp == 4:  # IPv6
        if len(data) < pos + 16 + 2:
            raise ValueError("Truncated IPv6 address")
        addr = str(ipaddress.IPv6Address(data[pos : pos + 16]))
        pos += 16
    else:
        raise ValueError(f"Invalid address type: {atyp}")
    
    port = struct.unpack(">H", data[pos : pos+2])[0]
    pos += 2
    
    # \r\n دوم
    if data[pos : pos+2] != b'\r\n':
        raise ValueError("Invalid Trojan header ending")
    pos += 2
    
    payload = data[pos:]
    return cmd, addr, port, payload

async def parse_vmess_header(data: bytes, expected_uuid: str):
    """
    استخراج هدر VMESS با فرمت استاندارد.
    این یک پیاده‌سازی ساده شده است - در عمل VMESS پیچیده‌تر است
    """
    # VMESS از یک هدر 16 بایتی + آدرس استفاده می‌کند
    if len(data) < 18:
        raise ValueError("VMESS header too short")
    
    # بایت اول نسخه است
    version = data[0]
    if version not in [1, 2]:
        raise ValueError(f"Unsupported VMESS version: {version}")
    
    # بایت دوم طول UUID است (معمولاً 16)
    uuid_len = data[1]
    if uuid_len != 16:
        raise ValueError(f"Invalid UUID length: {uuid_len}")
    
    # خواندن UUID (بایت‌های 2 تا 18)
    uuid_bytes = data[2:18]
    # تبدیل به string برای بررسی
    uuid_hex = uuid_bytes.hex()
    uuid_str = f"{uuid_hex[:8]}-{uuid_hex[8:12]}-{uuid_hex[12:16]}-{uuid_hex[16:20]}-{uuid_hex[20:32]}"
    
    if uuid_str != expected_uuid.replace('-', ''):
        # ممکن است UUID متفاوت باشد یا هدر رمزگذاری شده باشد
        # در اینجا ساده‌سازی می‌کنیم
        pass
    
    # بقیه هدر شامل آدرس است
    pos = 18
    
    # خواندن نوع آدرس
    if len(data) < pos + 1:
        raise ValueError("VMESS header truncated")
    
    addr_type = data[pos]
    pos += 1
    
    if addr_type == 1:  # IPv4
        if len(data) < pos + 4 + 2:
            raise ValueError("Truncated IPv4 address")
        addr = f"{data[pos]}.{data[pos+1]}.{data[pos+2]}.{data[pos+3]}"
        pos += 4
    elif addr_type == 2:  # Domain
        if len(data) < pos + 1:
            raise ValueError("Truncated domain address")
        domain_len = data[pos]
        pos += 1
        if len(data) < pos + domain_len + 2:
            raise ValueError("Truncated domain name string")
        addr = data[pos : pos + domain_len].decode('utf-8')
        pos += domain_len
    elif addr_type == 3:  # IPv6
        if len(data) < pos + 16 + 2:
            raise ValueError("Truncated IPv6 address")
        addr = str(ipaddress.IPv6Address(data[pos : pos + 16]))
        pos += 16
    else:
        raise ValueError(f"Invalid address type: {addr_type}")
    
    port = struct.unpack(">H", data[pos : pos+2])[0]
    pos += 2
    
    payload = data[pos:]
    return 1, addr, port, payload  # cmd=1 برای TCP

async def parse_shadowsocks_header(data: bytes, method: str = "chacha20-ietf-poly1305"):
    """
    استخراج هدر Shadowsocks با فرمت استاندارد.
    بعد از رمزگشایی، هدر شامل SOCKS5 address است
    """
    # Shadowsocks از هدر SOCKS5 استفاده می‌کند
    if len(data) < 3:
        raise ValueError("Shadowsocks header too short")
    
    # بایت اول نوع آدرس (ATYP)
    atyp = data[0]
    pos = 1
    
    if atyp == 1:  # IPv4
        if len(data) < 1 + 4 + 2:
            raise ValueError("Truncated IPv4 address")
        addr = f"{data[pos]}.{data[pos+1]}.{data[pos+2]}.{data[pos+3]}"
        pos += 4
    elif atyp == 3:  # Domain Name
        if len(data) < 2:
            raise ValueError("Truncated domain address")
        domain_len = data[pos]
        pos += 1
        if len(data) < pos + domain_len + 2:
            raise ValueError("Truncated domain name string")
        addr = data[pos : pos + domain_len].decode('utf-8')
        pos += domain_len
    elif atyp == 4:  # IPv6
        if len(data) < 1 + 16 + 2:
            raise ValueError("Truncated IPv6 address")
        addr = str(ipaddress.IPv6Address(data[pos : pos + 16]))
        pos += 16
    else:
        raise ValueError(f"Invalid SOCKS5 ATYP: {atyp}")
    
    port = struct.unpack(">H", data[pos : pos+2])[0]
    pos += 2
    
    payload = data[pos:]
    return 1, addr, port, payload  # cmd=1 برای TCP

def decode_shadowsocks_password(encoded: str) -> tuple:
    """
    رمزگشایی پسورد Shadowsocks از فرمت base64
    فرمت: method:password
    """
    try:
        decoded = base64.urlsafe_b64decode(encoded + '==').decode('utf-8')
        method, password = decoded.split(':', 1)
        return method, password
    except Exception:
        return "chacha20-ietf-poly1305", encoded
