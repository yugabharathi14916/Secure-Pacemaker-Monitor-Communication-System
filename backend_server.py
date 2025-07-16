# backend_server.py
import socket
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn
import logging

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# === Logging Setup ===
logging.basicConfig(
    filename="monitor_log.txt",
    level=logging.INFO,
    format="%(message)s"  # Clean log format, no debug clutter
)

def log_heartbeat(data):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"{timestamp} | {data}")

# === Heartbeat Storage ===
latest_heartbeat = "No data yet"

def handle_client(conn, addr):
    global latest_heartbeat
    print(f"[Monitor] Connection from {addr}")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            latest_heartbeat = data.decode().strip()
            print("[Monitor] Received:", latest_heartbeat)
            log_heartbeat(latest_heartbeat)
    except Exception as e:
        print(f"[Monitor] Error from {addr}: {e}")
    finally:
        conn.close()
        print(f"[Monitor] Disconnected from {addr}")

def socket_server():
    host = '0.0.0.0'
    port = 9999
    s = socket.socket()
    s.bind((host, port))
    s.listen()
    print("[Monitor] Listening for connections...")

    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

# Start socket server in background
threading.Thread(target=socket_server, daemon=True).start()

@app.get("/heartbeat")
def get_heartbeat():
    return {"heartbeat": latest_heartbeat}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
