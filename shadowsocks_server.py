# shadowsocks_server.py
import asyncio
import socket
import struct
import hashlib
import hmac
import os
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from state import LINKS, connections, logger, check_and_use

SS_PORT = int(os.environ.get("SS_PORT", 8388))
METHOD = "chacha20-ietf-poly1305"

def derive_key(password: str, salt: bytes = None) -> bytes:
    if salt is None:
        salt = b'\x00' * 16
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000, dklen=32)
    return key

class ShadowsocksServer:
    def __init__(self):
        self.server = None
        
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        client_addr = writer.get_extra_info('peername')
        logger.info(f"Shadowsocks client connected from {client_addr}")
        
        try:
            header = await reader.read(1024)
            if len(header) < 32:
                writer.close()
                return
            
            uuid = header[:36].decode('utf-8', errors='ignore')
            
            if uuid not in LINKS:
                logger.warning(f"Invalid UUID: {uuid}")
                writer.close()
                return
            
            addr_type = header[36] if len(header) > 36 else 1
            
            if addr_type == 1:
                addr = f"{header[37]}.{header[38]}.{header[39]}.{header[40]}"
                port = struct.unpack(">H", header[41:43])[0]
                pos = 43
            else:
                addr = "1.1.1.1"
                port = 443
                pos = 37
            
            payload = header[pos:]
            
            try:
                dest_reader, dest_writer = await asyncio.open_connection(addr, port)
            except Exception as e:
                logger.error(f"Failed to connect to {addr}:{port}: {e}")
                writer.close()
                return
            
            conn_id = f"ss-{id(writer)}"
            connections[conn_id] = {
                "uuid": uuid,
                "ip": str(client_addr[0]) if client_addr else "unknown",
                "connected_at": datetime.now().isoformat(),
                "bytes": 0,
                "transport": "shadowsocks"
            }
            
            if payload:
                dest_writer.write(payload)
                await dest_writer.drain()
            
            async def client_to_server():
                try:
                    while True:
                        data = await reader.read(8192)
                        if not data:
                            break
                        if not await check_and_use(uuid, len(data)):
                            break
                        connections[conn_id]["bytes"] += len(data)
                        dest_writer.write(data)
                        await dest_writer.drain()
                except Exception:
                    pass
                finally:
                    dest_writer.close()
            
            async def server_to_client():
                try:
                    while True:
                        data = await dest_reader.read(8192)
                        if not data:
                            break
                        if not await check_and_use(uuid, len(data)):
                            break
                        connections[conn_id]["bytes"] += len(data)
                        writer.write(data)
                        await writer.drain()
                except Exception:
                    pass
                finally:
                    writer.close()
            
            await asyncio.gather(client_to_server(), server_to_client())
            
        except Exception as e:
            logger.error(f"Shadowsocks error: {e}")
        finally:
            try:
                writer.close()
            except:
                pass
            for cid, conn in list(connections.items()):
                if conn.get("transport") == "shadowsocks" and conn.get("ip") == str(client_addr[0]):
                    del connections[cid]
                    break

    async def start(self, port: int = SS_PORT):
        self.server = await asyncio.start_server(
            self.handle_client, '0.0.0.0', port
        )
        logger.info(f"Shadowsocks server started on port {port}")
        async with self.server:
            await self.server.serve_forever()

async def start_shadowsocks_server(port: int = SS_PORT):
    server = ShadowsocksServer()
    await server.start(port)

if __name__ == "__main__":
    asyncio.run(start_shadowsocks_server())
