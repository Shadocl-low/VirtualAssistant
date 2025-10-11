import sys
import queue, threading, subprocess, yaml, time, websocket, json

from recognizer_vosk import VoskRecognizer
from audio_listener import AudioListener
from command_handler import CommandHandler
from tts_engine import TTSEngine

PORT = 8000

class AvatarClient:
    def __init__(self, ws_url="ws://localhost:8765"):
        self.ws_url = ws_url
        self.ws = None
        self.connected = False
        self.connect()

    def connect(self):
        def run():
            while True:
                try:
                    self.ws = websocket.create_connection(self.ws_url)
                    self.connected = True
                    print("✅ Connected to Electron Avatar")
                    break
                except Exception as e:
                    print(f"⏳ Waiting for Electron to start... ({e})")
                    time.sleep(2)
        threading.Thread(target=run, daemon=True).start()

    def send_param(self, name, value):
        if self.ws and self.connected:
            try:
                message = json.dumps({"param": {"name": name, "value": float(value)}})
                self.ws.send(message)
                print(f"📤 Sent param: {name} = {value}")
            except Exception as e:
                print(f"❌ Error sending param: {e}")
                self.connected = False

    def send_expression(self, expr):
        if self.ws and self.connected:
            try:
                message = json.dumps({"expression": expr})
                self.ws.send(message)
                print(f"🎭 Sent expression: {expr}")
            except Exception as e:
                print(f"❌ Error sending expression: {e}")
                self.connected = False

    def send_motion(self, motion_name):
        if self.ws and self.connected:
            try:
                message = json.dumps({"motion": motion_name})
                self.ws.send(message)
                print(f"🎬 Sent motion command: {motion_name}")
            except Exception as e:
                print(f"❌ Error sending motion command: {e}")


# --- Завантаження конфігурації ---
def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# --- Головна функція ---
def main():
    cfg = load_config()

    audio_q = queue.Queue()
    text_q = queue.Queue()
    level_q = queue.Queue()

    # Запуск Electron
    electron_project_path = cfg.get("electron_project_path")
    if electron_project_path:
        print(f"🚀 Launching Electron from folder: '{electron_project_path}'...")
        command = ["npx", "electron", "."]
        subprocess.Popen(command, shell=True, cwd=electron_project_path)
    else:
        print("⚠️ 'electron_project_path' not found in config.yaml. Skipping Electron launch.")

    # Підключення до Electron через WebSocket
    avatar = AvatarClient()

    # TTS
    tts = TTSEngine(
        voice="en-US-JennyNeural"
    )

    # Recognizer (Vosk)
    wake_words = cfg.get("wake_words", ["sparkle"])
    commands = cfg.get("commands", {})

    recognizer = VoskRecognizer(
        model_path=cfg["vosk"]["model_path"],
        audio_queue=audio_q,
        text_queue=text_q,
        wake_words=wake_words,
        commands=commands
    )

    # Command handler
    cmd_handler = CommandHandler(
        cfg.get("commands", {}),
        tts,
        avatar
    )

    # Audio listener
    audio_listener = AudioListener(audio_queue=audio_q, level_queue=level_q, cmd_handler=cmd_handler)

    # --- Потоки ---
    t1 = threading.Thread(target=audio_listener.run, daemon=True)
    t2 = threading.Thread(target=recognizer.run, daemon=True)
    t1.start()
    t2.start()

    # --- Основний цикл ---
    def poll_recognized():
        try:
            while True:
                text = text_q.get_nowait()
                if not text:
                    continue
                print("Визначено:", text)
                cmd_handler.handle(text)
        except queue.Empty:
            pass

        # Оновлення рота (ParamMouthOpenY) з level_q
        # max_l = 0.0
        # try:
        #     while True:
        #         l = level_q.get_nowait()
        #         if l > max_l:
        #             max_l = l
        # except queue.Empty:
        #     pass
        # mouth_open = min(max_l * 5.0, 1.0)
        # avatar.send_param("ParamMouthOpenY", mouth_open)

        # повторний виклик через 50 мс
        threading.Timer(0.05, poll_recognized).start()

    poll_recognized()

    return tts

if __name__ == "__main__":
    tts_engine = main()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Коли програма закривається (Ctrl+C), коректно зупиняємо TTS
        print("Застосунок закривається, зупиняємо TTS...")
        tts_engine.shutdown()
