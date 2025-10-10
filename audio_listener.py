import sounddevice as sd
import numpy as np
import queue
import time

class AudioListener:
    def __init__(self, samplerate=16000, blocksize=1600, audio_queue=None, level_queue=None, cmd_handler=None):
        self.sr = samplerate
        self.block = blocksize
        self.audio_q = audio_queue
        self.level_q = level_queue
        self.stream = None
        self.cmd_handler = cmd_handler

    def _callback(self, indata, frames, time_info, status):
        # `indata` - це сирий буфер (raw buffer), а не NumPy array.

        # 1. Просто передаємо буфер в чергу для Vosk.
        #    Він вже є байтами, тому .tobytes() не потрібен.
        if self.audio_q is not None:
            self.audio_q.put(indata)

        # 2. Для розрахунку гучності створюємо NumPy array з буфера.
        if self.level_q is not None:
            try:
                # Створюємо NumPy array з raw buffer, вказуючи тип даних.
                np_indata = np.frombuffer(indata, dtype=np.int16)

                # Подальші розрахунки ідентичні попереднім.
                float_data = np_indata.astype(np.float32) / 32768.0
                rms = np.sqrt(np.mean(float_data**2))
                self.level_q.put_nowait(rms)
            except queue.Full:
                pass

    def run(self):
        try:
            with sd.RawInputStream(channels=1, samplerate=self.sr, blocksize=self.block,
                                   callback=self._callback, dtype='int16'):
                print("🎤 Audio listener started correctly...")
                self.cmd_handler.handle("chill")
                while True:
                    time.sleep(1)
        except Exception as e:
            print(f"❌ Помилка в AudioListener: {e}")