import sounddevice as sd
import numpy as np
import queue
import time

class AudioListener:
    def __init__(self, samplerate=16000, blocksize=8000, audio_queue=None, level_queue=None):
        self.sr = samplerate
        self.block = blocksize
        self.audio_q = audio_queue
        self.level_q = level_queue
        self.stream = None

    def _callback(self, indata, frames, time_info, status):
        # indata is shape (frames, channels)
        mono = np.mean(indata, axis=1)
        # convert to 16-bit PCM
        pcm = (mono * 32767).astype('int16').tobytes()
        if self.audio_q is not None:
            self.audio_q.put(pcm)
        # RMS level for avatar animation
        rms = np.sqrt(np.mean(mono**2))
        if self.level_q is not None:
            try:
                self.level_q.put_nowait(rms)
            except queue.Full:
                pass

    def run(self):
        with sd.InputStream(channels=1, samplerate=self.sr, blocksize=self.block,
                            callback=self._callback, dtype='float32'):
            while True:
                time.sleep(0.1)
