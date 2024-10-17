import asyncio
import websockets
import cv2
import json
import numpy as np

# URL del servidor WebSocket
uri = "ws://localhost:8000/ws"

async def send_video(websocket):
    cap = cv2.VideoCapture(0)  # 0 para la cámara web predeterminada

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error al capturar el frame")
                break

            _, buffer = cv2.imencode('.jpg', frame)
            bytes_frame = buffer.tobytes()

            # Crear un diccionario con los datos
            data = {
                'id_member': None,  # O puedes especificar un ID si es necesario
                'bytes_array': list(bytes_frame),
                'data_type': '__video__'
            }

            # Convertir el diccionario a JSON y luego a bytes
            json_data = json.dumps(data)
            await websocket.send(json_data)

            await asyncio.sleep(1 / 30)  # Esperar para mantener aproximadamente 30 FPS

    except Exception as e:
        print(f"Error durante la transmisión: {e}")
    finally:
        cap.release()

async def receive_video(websocket):
    while True:
        try:
            message = await websocket.recv()
            data = json.loads(message)

            if "bytes_array" in data:
                bytes_array = bytearray(data["bytes_array"])
                np_array = np.frombuffer(bytes_array, dtype=np.uint8)
                frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

                if frame is not None:
                    cv2.imshow("Received Video", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

        except Exception as e:
            print(f"Error al recibir el video: {e}")
            break

async def main():
    async with websockets.connect(uri) as websocket:
        await asyncio.gather(send_video(websocket), receive_video(websocket))

if __name__ == "__main__":
    asyncio.run(main())
    cv2.destroyAllWindows()
