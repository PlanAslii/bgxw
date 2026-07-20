# relay_protocols.py
import struct
import ipaddress
import hashlib
from state import LINKS, is_link_allowed

async def check_and_use(uuid: str, nbytes: int) -> bool:
    """بررسی مجاز بودن کاربر و کسر حجم به صورت در لحظه"""
    link = LINKS.get(uuid)
    if not is_link_allowed(link):
        return False
    if link:
        link["used_bytes"] += nbytes
    return True

async def parse_vless_header(data: bytes):
    """
    استخراج هدر استاندارد VLESS.
    فرمت: Version(1) + UUID(16) + OptLen(1) + CMD(1) + Port(2) + Atyp(1) + Addr + Payload
    توجه: UUID در اینجا نادیده گرفته می‌شود چون از مسیر URL در FastAPI استخراج شده است.
    """
    if len(data) < 24:
        raise ValueError("VLESS header is too short")
        
    version = data[0]
    opt_len = data[17]
    cmd = data[18 + opt_len] # 1: TCP, 2: UDP
    port = struct.unpack(">H", data[19 + opt_len : 21 + opt_len])[0]
    addr_type = data[21 + opt_len]
    pos = 22 + opt_len

    if addr_type == 1: # IPv4
        addr = f"{data[pos]}.{data[pos+1]}.{data[pos+2]}.{data[pos+3]}"
        pos += 4
    elif addr_type == 2: # Domain
        domain_len = data[pos]
        pos += 1
        addr = data[pos : pos + domain_len].decode('utf-8')
        pos += domain_len
    elif addr_type == 3: # IPv6
        addr = str(ipaddress.IPv6Address(data[pos : pos + 16]))
        pos += 16
    else:
        raise ValueError(f"Unknown address type: {addr_type}")

    payload = data[pos:]
    return cmd, addr, port, payload

async def parse_socks5_address(data: bytes):
    """
    استخراج آدرس SOCKS5 که در هدر دیتای Shadowsocks پس از رمزگشایی قرار دارد.
    برمی‌گرداند: (نوع آدرس, آدرس مقصد, پورت مقصد, طول هدر آدرس)
    """
    if not data:
        raise ValueError("Empty SOCKS5 address data")
        
    atyp = data[0]
    pos = 1
    
    if atyp == 1: # IPv4
        if len(data) < 7: raise ValueError("Truncated IPv4 address")
        addr = f"{data[pos]}.{data[pos+1]}.{data[pos+2]}.{data[pos+3]}"
        pos += 4
    elif atyp == 3: # Domain Name
        if len(data) < 2: raise ValueError("Truncated domain address")
        domain_len = data[pos]
        pos += 1
        if len(data) < pos + domain_len + 2: raise ValueError("Truncated domain name string")
        addr = data[pos : pos + domain_len].decode('utf-8')
        pos += domain_len
    elif atyp == 4: # IPv6
        if len(data) < 19: raise ValueError("Truncated IPv6 address")
        addr = str(ipaddress.IPv6Address(data[pos : pos + 16]))
        pos += 16
    else:
        raise ValueError(f"Invalid SOCKS5 ATYP: {atyp}")
        
    port = struct.unpack(">H", data[pos : pos+2])[0]
    pos += 2
    
    return atyp, addr, port, pos
        addr = str(ipaddress.IPv6Address(data[pos : pos + 16]))
        pos += 16
    else:
        raise ValueError(f"Unknown address type: {atyp}")
        
    port = struct.unpack(">H", data[pos : pos+2])[0]
    pos += 2
    
    # \r\n دوم
    if data[pos : pos+2] != b'\r\n':
        raise ValueError("Invalid Trojan header ending")
    pos += 2
    
    payload = data[pos:]
    return cmd, addr, port, payload
