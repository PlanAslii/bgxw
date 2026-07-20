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

async def parse_trojan_header(data: bytes, expected_uuid: str):
    """
    استخراج هدر استاندارد Trojan.
    فرمت: Hex(SHA224(Password))(56) + \r\n + CMD(1) + ATYP(1) + DST.ADDR + DST.PORT(2) + \r\n + Payload
    ما از UUID به عنوان پسورد تروجان استفاده کرده‌ایم.
    """
    if len(data) < 60:
        raise ValueError("Trojan header is too short")
        
    # پیدا کردن اولین جداکننده \r\n
    idx1 = data.find(b'\r\n')
    if idx1 == -1 or idx1 != 56:
        raise ValueError("Invalid Trojan password format or missing CRLF")
        
    received_hash = data[:56].decode('ascii')
    expected_hash = hashlib.sha224(expected_uuid.encode('utf-8')).hexdigest()
    
    if received_hash != expected_hash:
        raise ValueError("Trojan Authentication Failed: Password Hash Mismatch")

    cmd = data[idx1+2] # 1: CONNECT (TCP), 3: UDP ASSOCIATE
    atyp = data[idx1+3]
    pos = idx1+4
    
    if atyp == 1: # IPv4
        addr = f"{data[pos]}.{data[pos+1]}.{data[pos+2]}.{data[pos+3]}"
        pos += 4
    elif atyp == 3: # Domain
        domain_len = data[pos]
        pos += 1
        addr = data[pos : pos + domain_len].decode('utf-8')
        pos += domain_len
    elif atyp == 4: # IPv6
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
