import serial
import socket
import time
import serial.tools.list_ports
from datetime import datetime
import threading

LOG_FILE = "/home/hp/pacemaker_log.txt"
TARGET_BPM = 72

latest_attack_bpm = None

def log_event(event):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} {event}\n")

def find_arduino_port():
    print("[Pacemaker] Scanning ports...")
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "ttyACM" in port.device or "Arduino" in port.description:
            print(f"  {port.device}: {port.description}")
            return port.device
    return None

def evaluate_and_correct_bpm(bpm):
    if bpm < 50:
        diff = TARGET_BPM - bpm
        corrected = bpm + diff
        status = f"Impulse delivered for bradycardia | BPM : {bpm} | Feedback: +{diff}"
    elif bpm > 130:
        diff = bpm - TARGET_BPM
        corrected = bpm - diff
        status = f"Tachycardia detected — alert sent | BPM : {bpm} | Feedback: -{diff}"
    else:
        corrected = bpm
        status = "Normal"
    return corrected, status

def start_attacker_server():
    global latest_attack_bpm
    server = socket.socket()
    server.bind(("0.0.0.0", 7777))
    server.listen(1)

    conn, addr = server.accept()
    log_event(f"[Attacker] Connected from {addr}")

    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            decoded = data.decode().strip()
            if decoded.startswith("Heartbeat"):
                bpm = int(decoded.split(":")[1].split()[0])
                latest_attack_bpm = bpm
                log_event(f"[Attacker Injected BPM] {bpm}")
        except Exception as e:
            log_event(f"[Attacker Error] {e}")
            break

    conn.close()
    log_event("[Attacker] Disconnected")

def main():
    global latest_attack_bpm

    arduino_port = find_arduino_port()
    if not arduino_port:
        print("[Pacemaker] Arduino not found.")
        log_event("Arduino not found.")
        return

    try:
        arduino = serial.Serial(arduino_port, 9600, timeout=1)
        print(f"[Pacemaker] Connected to Arduino on {arduino_port}")
        log_event(f"Connected to Arduino on {arduino_port}")
    except Exception as e:
        print(f"[Pacemaker] Failed to connect to Arduino: {e}")
        log_event(f"Failed to connect to Arduino: {e}")
        return

    threading.Thread(target=start_attacker_server, daemon=True).start()

    monitor_ip = "10.179.212.68"
    monitor_port = 9999

    try:
        sock = socket.socket()
        sock.connect((monitor_ip, monitor_port))
        print(f"[Pacemaker] Connected to Monitor at {monitor_ip}:{monitor_port}")
        log_event(f"Connected to Monitor at {monitor_ip}:{monitor_port}")
    except Exception as e:
        print("[Pacemaker] Failed to connect to monitor:", e)
        log_event(f"Failed to connect to monitor: {e}")
        return

    print("[Pacemaker] Sending heartbeat data to monitor...")
    log_event("Started sending heartbeat data.")

    while True:
        try:
            if arduino.in_waiting > 0:
                line = arduino.readline().decode().strip()

                if line.startswith("BPM:"):
                    real_bpm = int(line.split(":")[1])
                    manipulated_bpm = real_bpm

                    if latest_attack_bpm is not None:
                        # Attack active — add difference to real BPM and bypass correction
                        diff = abs(TARGET_BPM - latest_attack_bpm)
                        manipulated_bpm = real_bpm + diff
                        print(f"[Real BPM] {real_bpm} bpm")
                        print(f"Spiked BPM: {manipulated_bpm}")
                        msg = f"Heartbeat: {manipulated_bpm} bpm | Status: Uncontrolled impulse (attack successful)"
                        latest_attack_bpm = None
                    else:
                        # No attack — normal pacemaker logic
                        corrected_bpm, status = evaluate_and_correct_bpm(manipulated_bpm)
                        msg = f"Heartbeat: {corrected_bpm} bpm | Status: {status}"

                    print("[Pacemaker]", msg)
                    sock.sendall((msg + "\n").encode())
                    log_event(msg)

        except Exception as e:
            print("[Pacemaker] Error:", e)
            log_event(f"Error: {e}")
            break

    arduino.close()
    sock.close()
    log_event("Closed all connections.")

if __name__ == "__main__":
    main()
