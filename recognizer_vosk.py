from vosk import Model, KaldiRecognizer
import json
import queue
import time

class VoskRecognizer:
    def __init__(self, model_path, audio_queue: queue.Queue, text_queue: queue.Queue,
                 wake_words: list, commands: dict, sr=16000, command_timeout=15):

        print("🎧 Initializing recognizer with wake-word functionality...")

        self.audio_q = audio_queue
        self.text_q = text_queue
        self.command_timeout = command_timeout  # Час у секундах на очікування команди
        self.wake_words = wake_words

        model = Model(model_path)

        # 1. Створюємо легкий розпізнавач ТІЛЬКИ для wake-words
        # [unk] дозволяє ігнорувати невідомі слова, що підвищує точність
        wake_word_grammar = json.dumps(wake_words + ["[unk]"])
        self.wake_word_recognizer = KaldiRecognizer(model, sr, wake_word_grammar)
        print(f"👂 Listening for wake words: {wake_words}")

        # 2. Створюємо основний розпізнавач для всіх команд
        # Для кращої точності можна створити граматику з усіх команд
        command_phrases = list(commands.keys())
        self.command_recognizer = KaldiRecognizer(model, sr, json.dumps(command_phrases + ["[unk]"]))
        print(f"💬 Ready to listen for {len(command_phrases)} commands after wake-word.")

        # Початковий стан асистента
        self.is_awake = False
        self.wakeup_time = 0

    def run(self):
        while True:
            audio_data = self.audio_q.get()
            if audio_data is None:
                break

            if not self.is_awake:
                # --- РЕЖИМ 1: ОЧІКУВАННЯ WAKE-WORD ---
                if self.wake_word_recognizer.AcceptWaveform(bytes(audio_data)):
                    result = json.loads(self.wake_word_recognizer.Result())
                    text = result.get('text', '').strip()
                    # Перевіряємо, чи розпізнаний текст є одним з wake-words
                    if any(word in text for word in self.wake_words):
                        print("\n✨ Wake-word detected! Listening for command...")
                        self.is_awake = True
                        self.wakeup_time = time.time()
            else:
                # --- РЕЖИM 2: АКТИВНЕ СЛУХАННЯ КОМАНДИ ---
                # Перевірка на таймаут
                if time.time() - self.wakeup_time > self.command_timeout:
                    print("🌙 Command timeout. Going back to sleep.")
                    self.is_awake = False
                    # Скидаємо буфер розпізнавача, щоб уникнути залишків мови
                    self.command_recognizer.Reset()
                    continue

                if self.command_recognizer.AcceptWaveform(bytes(audio_data)):
                    result = json.loads(self.command_recognizer.Result())
                    command_text = result.get('text', '').strip()

                    if command_text and command_text != "[unk]":
                        print(f"✅ Command heard: '{command_text}'")
                        self.text_q.put(command_text)
                        self.is_awake = False # Повертаємось у сплячий режим після команди
                        self.command_recognizer.Reset()