import json
import uuid
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict

app = FastAPI()

# Diccionario de conexiones activas: {connection_id: WebSocket}
active_connections: Dict[str, WebSocket] = {}

""" Send data to all members connected """
async def broadcast_all_members(message: dict) -> None:
    print("MM -> ", active_connections)
    for member_id, member_ws in active_connections.items():
        try:
            member_list = [conn_id for conn_id in active_connections.keys() if conn_id != member_id]
            await member_ws.send_json({"member_list": member_list, "message": message})
        except Exception as e:
            print(f"Error al enviar lista a {member_id}: {e}")



""" Send data to a specific member ID """
async def send_data_to_specific_member(member_id: str, message: dict) -> None:
    websocket = active_connections.get(member_id)
    if websocket:
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error al enviar mensaje a {member_id}: {e}")



""" Send bytes to all members connected """
async def broadcast_bytes_all_members(message: bytes) -> None:
    for member_id, member_ws in active_connections.items():
        try:
            print("Enviando ->", type(message))
            await member_ws.send_bytes(message)
        except Exception as e:
            print(f"Error al enviar los bytes {member_id}: {e}")



""" Send bytes to specific member connected """
async def send_bytes_to_specific_member(member_id: str, message: bytes) -> None:
    websocket = active_connections.get(member_id)
    if websocket:
        try:
            await websocket.send_bytes(message)
        except Exception as e:
            print(f"Error al enviar bytes a {member_id}: {e}")



""" Remove disconnected member of the list """
async def handle_disconnection(conn_id: str) -> None:
    if conn_id in active_connections:
        del active_connections[conn_id]
        await broadcast_all_members({})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connection_id = str(uuid.uuid4())

    if connection_id not in active_connections:
        active_connections[connection_id] = websocket
        await broadcast_all_members({})

    try:
        while True:
            data = await websocket.receive()
            # Verifica si los datos son binarios
            if isinstance(data, dict) and "text" in data:
                data_retrieved = json.loads(data["text"])
                data_type = data_retrieved["data_type"]
                member_id = data_retrieved["id_member"]
                if data_type == "__video__":
                    bytes_array = bytearray(data_retrieved["bytes_array"])
                    if member_id:
                        await send_bytes_to_specific_member(member_id, bytes_array)
                    else:
                        await broadcast_bytes_all_members(bytes_array)
                if data_type == "__image__":
                    pass
                if data_type == "__audio__":
                    pass

    except WebSocketDisconnect:
        await handle_disconnection(connection_id)

    except Exception as e:
        await handle_disconnection(connection_id)
        print(f"Error general: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, ws_ping_interval=10, ws_ping_timeout=20)
