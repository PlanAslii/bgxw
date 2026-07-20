# relay_protocols.py
import struct
import ipaddress
import hashlib
import base64
import json
from state import LINKS, is_link_allowed

async def check_and_use(uuid: str, nbytes: int) -> bool:
    link = LINKS.get(uuid)
    if not is_link_allowed(link):
        return False
    if link:
        link["used_bytes"] = link.get("used_bytes", 0) + nbytes
    return True

async def parse_vless_header(data: bytes):
    if len(data) < 24:
        raise ValueError("VLESS header is too short")
    version = data[0]
    opt_len = data[17]
    cmd = data[18 + opt_len]
    port = struct.unpack(">H", data[19 + opt_len : 21 + opt_len])[0]
    addr_type = data[21 + opt_len]
    pos = 22 + opt_len
    if addr_type == 1:
        addr = f"{data[pos]}.{data[pos+1]}.{data[pos+2]}.{data[pos+3]}"
        pos += 4
    elif addr_type == 2:
        domain_len = data[pos]
        pos += 1
        addr = data[pos : pos + domain_len].decode('utf-8')
        pos += domain_len
    elif addr_type == 3:
        addr = str(ipaddress.IPv6Address(data[pos : pos + 16]))
        pos += 16
    else:
        raise ValueError(f"Unknown address type: {addr_type}")
    payload = data[pos:]
    return cmd, addr, port, payload

async def parse_trojan_header(data: bytes, expected_uuid: str):
    crlf_pos = data.find(b'\r\n')
    if crlf_pos == -1:
        raise ValueError("Invalid Trojan header: no CRLF found")
    password = data[:crlf_pos].decode('utf-8')
    if password != expected_uuid:
        raise ValueError(f"Invalid Trojan password")
    pos = crlf_pos + 2
    if len(data) < pos + 1:
        raise ValueError("Trojan header too short")
    cmd = data[pos]
    pos += 1
    atyp = data[pos]
    pos += 1
    if atyp == 1:
        if len(data) < pos + 4 + 2:
            raise ValueError("Truncated IPv4 address")
        addr = f"{data[pos]}.{data[pos+1]}.{data[pos+2]}.{data[pos+3]}"
        pos += 4
    elif atyp == 3:
        if len(data) < pos + 1:
            raise ValueError("Truncated domain address")
        domain_len = data[pos]
        pos += 1
        if len(data) < pos + domain_len + 2:
            raise ValueError("Truncated domain name string")
        addr = data[pos : pos + domain_len].decode('utf-8')
        pos += domain_len
    elif atyp == 4:
        if len(data) < pos + 16 + 2:
            raise ValueError("Truncated IPv6 address")
        addr = str(ipaddress.IPv6Address(data[pos : pos + 16]))
        pos += 16
    else:
        raise ValueError(f"Invalid address type: {atyp}")
    port = struct.unpack(">H", data[pos : pos+2])[0]
    pos += 2
    if data[pos : pos+2] != b'\r\n':
        raise ValueError("Invalid Trojan header ending")
    pos += 2
    payload = data[pos:]
    return cmd, addr, port, payload

async def parse_vmess_header(data: bytes, expected_uuid: str):
    if len(data) < 18:
        raise ValueError("VMESS header too short")
    version = data[0]
    if version not in [1, 2]:
        raise ValueError(f"Unsupported VMESS version: {version}")
    uuid_len = data[1]
    if uuid_len != 16:
        raise ValueError(f"Invalid UUID length: {uuid_len}")
    pos = 18
    if len(data) < pos + 1:
        raise ValueError("VMESS header truncated")
    addr_type = data[pos]
    pos += 1
    if addr_type == 1:
        if len(data) < pos + 4 + 2:
            raise ValueError("Truncated IPv4 address")
        addr = f"{data[pos]}.{data[pos+1]}.{data[pos+2]}.{data[pos+3]}"
        pos += 4
    elif addr_type == 2:
        if len(data) < pos + 1:
            raise ValueError("Truncated domain address")
        domain_len = data[pos]
        pos += 1
        if len(data) < pos + domain_len + 2:
            raise ValueError("Truncated domain name string")
        addr = data[pos : pos + domain_len].decode('utf-8')
        pos += domain_len
    elif addr_type == 3:
        if len(data) < pos + 16 + 2:
            raise ValueError("Truncated IPv6 address")
        addr = str(ipaddress.IPv6Address(data[pos : pos + 16]))
        pos += 16
    else:
        raise ValueError(f"Invalid address type: {addr_type}")
    port = struct.unpack(">H", data[pos : pos+2])[0]
    pos += 2
    payload = data[pos:]
    return 1, addr, port, payload

async def parse_shadowsocks_header(data: bytes):
    if len(data) < 3:
        raise ValueError("Shadowsocks header too short")
    atyp = data[0]
    pos = 1
    if atyp == 1:
        if len(data) < 1 + 4 + 2:
            raise ValueError("Truncated IPv4 address")
        addr = f"{data[pos]}.{data[pos+1]}.{data[pos+2]}.{data[pos+3]}"
        pos += 4
    elif atyp == 3:
        if len(data) < 2:
            raise ValueError("Truncated domain address")
        domain_len = data[pos]
        pos += 1
        if len(data) < pos + domain_len + 2:
            raise ValueError("Truncated domain name string")
        addr = data[pos : pos + domain_len].decode('utf-8')
        pos += domain_len
    elif atyp == 4:
        if len(data) < 1 + 16 + 2:
            raise ValueError("Truncated IPv6 address")
        addr = str(ipaddress.IPv6Address(data[pos : pos + 16]))
        pos += 16
    else:
        raise ValueError(f"Invalid SOCKS5 ATYP: {atyp}")
    port = struct.unpack(">H", data[pos : pos+2])[0]
    pos += 2
    payload = data[pos:]
    return 1, addr, port, payload
