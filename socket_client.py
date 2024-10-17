import os
import json
import hmac
import base64
import hashlib
import asyncio
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

HOST = "127.0.0.1"
PORT = 12000
key = b'Hassi2016!'  # Clave secreta utilizada para la firma

# Generar una clave de 128 bits (16 bytes)
key = os.urandom(16)
# Inicializar vector (IV) de 16 bytes
iv = os.urandom(16)
IV_SIZE = 16
# Crear el cifrador AES en modo CBC

message_to_sent = ""
member_list = []

def bytes_to_base64(byte_data: bytes) -> str:
    base64_encoded = base64.b64encode(byte_data)
    base64_string = base64_encoded.decode('utf-8')
    return base64_string

def base64_to_bytes(base64_string: str) -> bytes:
    byte_data = base64.b64decode(base64_string)
    return byte_data

def encrypt_AES_128(plaintext: str) -> str:
    plaintext_bytes = plaintext.encode('utf-8')
    iv = get_random_bytes(IV_SIZE)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_data = pad(plaintext_bytes, AES.block_size)
    ciphertext = cipher.encrypt(padded_data)
    encrypted_message = iv + ciphertext
    return bytes_to_base64(encrypted_message)

def decrypt_AES_128(ciphertext_base64: str) -> str:
    encrypted_message = base64_to_bytes(ciphertext_base64)
    iv = encrypted_message[:IV_SIZE]
    ciphertext = encrypted_message[IV_SIZE:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_plaintext = cipher.decrypt(ciphertext)
    plaintext_bytes = unpad(padded_plaintext, AES.block_size)
    return plaintext_bytes.decode('utf-8')

def sign_message(message: str) -> str:
    message_bytes = message.encode('utf-8')
    hmac_obj = hmac.new(key, message_bytes, hashlib.sha256)
    signature = hmac_obj.hexdigest()
    return signature

def verify_signature(message: str, signature: str) -> bool:
    message_bytes = message.encode('utf-8')
    hmac_obj = hmac.new(key, message_bytes, hashlib.sha256)
    expected_signature = hmac_obj.hexdigest()
    return hmac.compare_digest(expected_signature, signature)

async def run_socket_client() -> None:
    reader, writer = await asyncio.open_connection(HOST, PORT)
    message_ready = encrypt_AES_128(message_to_sent)
    final_message = {
        "type": "__test__", 
        "member_id": None, 
        "message": message_ready,
        "message_signature": sign_message(message_ready)
    }
    encoded_message = json.dumps(final_message).encode()
    writer.write(encoded_message)
    await writer.drain()

    while True:
        try:
            data = await reader.read(5120)
            if not data:
                raise Exception("Socket closed!")
            decoded_data = json.loads(data.decode('utf-8'))
            if decoded_data["type"] == "__members__":
                global member_list
                member_list = decoded_data["member_list"]
            if decoded_data["type"] == "__message__":
                if verify_signature(decoded_data["message"], decoded_data["message_signature"]):
                    decrypted_message = decrypt_AES_128(decoded_data["message"])
                    print("Message -> ", decrypted_message)
        except Exception as err:
            print("There was an error: ", err)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(run_socket_client())