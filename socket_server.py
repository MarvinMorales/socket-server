import json
import uuid
import socket
import asyncio
from typing import Dict
# 0989384386 -> 

HOST = "127.0.0.1"
PORT = 12000
CONN_MODE = "__conn__"
DIS_MODE = "__dis__"
QUIT = "__quit__"

## Collection of every client connected
active_connections: Dict[str, socket.socket] = {}

async def handle_emit_message(message: dict, current_id: str, member_id_target: str | None = None) -> None:
    try:
        if member_id_target:
            writer = active_connections[member_id_target]
            writer.write(json.dumps(message).encode())
        if not member_id_target:
            for _id, writer in active_connections.items():
                if _id != current_id:
                    writer.write(json.dumps(message).encode())
        await writer.drain()
    except Exception as err:
        print("There was an error in handle_emit_message -> ", err)

async def handle_connections(writer: asyncio.StreamWriter, _id: str, mode: str) -> None:
    try:
        if mode == CONN_MODE and _id not in active_connections:
            active_connections[_id] = writer
        elif mode == DIS_MODE and _id in active_connections:
            del active_connections[_id]
        for user_id, writer in active_connections.items():
            member_list = [_ for _ in active_connections.keys() if user_id != _]
            connections_message = {"type": "__members__", "member_list": member_list}
            writer.write(json.dumps(connections_message).encode())
        await writer.drain()
    except Exception as err:
        print("There was an error in handle_connections -> ", err)

async def handle_socket_data(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        connection_id = str(uuid.uuid4())
        await handle_connections(writer, connection_id, CONN_MODE)
        data = None
        while data != QUIT:
            primitive_data = await reader.read(5120)
            primitive_data = json.loads(primitive_data.decode("utf-8"))
            data = primitive_data["type"]
            message = primitive_data["message"]
            signature = primitive_data["message_signature"]
            member_id = primitive_data["member_id"]
            new_message = {"type": "__message__", "sent_by": connection_id, "message": message, "message_signature": signature}
            await handle_emit_message(new_message, connection_id, member_id)
        writer.close()
        await writer.wait_closed()
    except Exception as err:
        print("There was a error ->", err)
        await handle_connections(writer, connection_id, DIS_MODE)


async def run_socket_server() -> None:
    try:
        server = await asyncio.start_server(handle_socket_data, HOST, PORT)
        async with server:
            await server.serve_forever()
    except Exception as err:
        print("There was an error in run_socket_server -> ", err)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(run_socket_server())
    print(f"Server running on port: {PORT}")