import threading
import queue
import asyncio
import traceback
import os
import tempfile
from playsound import playsound
import edge_tts

class TTSEngine:
    def __init__(self, voice="uk-UA-PolinaNeural"):
        """
        Ініціалізує чергу та запускає потік-працівник для edge-tts.
        """
        self.queue = queue.Queue()
        # Ви можете знайти інші голоси командою: edge-tts --list-voices
        self.voice = voice

        # Запускаємо потік-працівник
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        print(f"🔊 TTS (edge-tts) worker started with voice: {self.voice}")

    def _process_queue(self):
        """
        Створює та запускає асинхронний цикл для обробки черги.
        """
        # Створюємо новий асинхронний цикл для цього потоку
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Запускаємо асинхронну функцію-працівника
        try:
            loop.run_until_complete(self._async_worker())
        finally:
            loop.close()

    async def _async_worker(self):
        """
        Асинхронно отримує текст з черги, синтезує мову і відтворює її.
        """
        while True:
            try:
                # Асинхронно чекаємо на елемент з черги
                text = await asyncio.to_thread(self.queue.get)

                if text is None:
                    break

                print(f"🎯 TTS (edge-tts): Processing '{text}'")

                # Синтезуємо мову
                communicate = edge_tts.Communicate(text, self.voice)

                # Створюємо тимчасовий файл для аудіо
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                    tmp_filename = fp.name

                # Асинхронно зберігаємо аудіо у файл
                await communicate.save(tmp_filename)

                # Відтворюємо звук (playsound - блокуюча функція)
                try:
                    playsound(tmp_filename)
                except Exception as e:
                    print(f"❌ Помилка відтворення звуку: {e}")
                finally:
                    # Гарантовано видаляємо тимчасовий файл
                    os.remove(tmp_filename)

                print("✅ TTS (edge-tts): Finished.")

            except Exception as e:
                print(f"❌ Помилка в TTS потоці-працівнику: {e}")
                traceback.print_exc()

    def speak(self, text):
        """
        Додає текст у чергу на озвучення.
        """
        if not text or not text.strip():
            return
        self.queue.put(text)

    def shutdown(self):
        """
        Коректно завершує роботу потоку-працівника.
        """
        print("⏹️ TTS: Завершення роботи...")
        self.queue.put(None)
        self.worker_thread.join(timeout=2)
        print("TTS потік-працівник зупинено.")