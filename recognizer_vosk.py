from vosk import Model, KaldiRecognizer
import json
import queue
import time

class VoskRecognizer:
    def __init__(self, model_path, audio_queue: queue.Queue, text_queue: queue.Queue,
                 commands: dict, sr=16000):
        self.audio_q = audio_queue
        self.text_q = text_queue
        self.commands = commands or {}

        model = Model(model_path)
        self.recognizer = KaldiRecognizer(model, sr)

        self.last_command = ""
        self.last_time = 0
        self.min_interval = 1.0

    def run(self):
        print("🎧 Voice recognizer started...")
        last_partial = ""
        while True:
            audio_data = self.audio_q.get() # Отримуємо _cffi_backend.buffer
            if audio_data is None:
                break

            # ✅ ОСЬ ВИПРАВЛЕННЯ: Перетворюємо буфер на bytes перед передачею
            if self.recognizer.AcceptWaveform(bytes(audio_data)):
                result_text = json.loads(self.recognizer.Result()).get('text', '')
                if result_text:
                    command = self._match_command(result_text)
                    if command:
                        now = time.time()
                        if command != self.last_command or (now - self.last_time) > self.min_interval:
                            self.text_q.put(command)
                            print(f"✅ Final command recognized: {command}")
                            self.last_command = command
                            self.last_time = now
                    last_partial = ""
            else:
                partial_text = json.loads(self.recognizer.PartialResult()).get('partial', '')
                if partial_text and partial_text != last_partial:
                    print(f"🎤 Hearing: {partial_text}")
                    last_partial = partial_text

    def _match_command(self, text: str):
        text = text.strip().lower()
        if not text:
            return None

        for cmd in self.commands.keys():
            if cmd in text:
                return cmd
        return None