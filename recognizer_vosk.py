from vosk import Model, KaldiRecognizer
import json
import queue
import time
import struct
import numpy as np

class VoskRecognizer:
    def __init__(self, model_path, audio_queue: queue.Queue, text_queue: queue.Queue,
                 commands: dict, sr=16000):
        self.audio_q = audio_queue
        self.text_q = text_queue
        self.commands = commands or {}

        self.recognizer = KaldiRecognizer(Model(model_path), sr)

        # Дебаунс команд
        self.last_command = ""
        self.last_time = 0
        self.min_interval = 1.0  # секунда між однаковими командами

    def run(self):
        print("🎧 Voice recognizer started...")
        while True:
            audio_data = self.audio_q.get()
            if audio_data is None:
                break

            if self.recognizer.AcceptWaveform(audio_data):
                result = json.loads(self.recognizer.Result())
                text = result.get('text', '').strip().lower()

                if not text:
                    continue

                command = self._match_command(text)
                if command:
                    now = time.time()
                    if command != self.last_command or (now - self.last_time) > self.min_interval:
                        self.text_q.put(command)
                        print(f"✅ Command recognized: {command}")
                        self.last_command = command
                        self.last_time = now

    def _match_command(self, text: str):
        for cmd in self.commands.keys():
            if cmd in text:
                return cmd
        return None
