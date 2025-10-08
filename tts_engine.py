import os
import threading
import tempfile
import traceback


class SimpleRVCTTSEngine:
    def __init__(self, rvc_model_path=None, rvc_index_path=None, voice_index=1, device='cpu'):
        self.voice_index = voice_index
        self.is_speaking = False
        self._current_thread = None
        self.rvc_converter = None
        self.use_rvc = False
        print("🔊 Обычный TTS режим")

    def speak(self, text):
        """Озвучить текст"""
        if not text or not text.strip():
            return

        if self.is_speaking:
            self.stop()

        self.is_speaking = True
        print(f"🎯 TTS: Обрабатываю '{text}'")

        def _process():
            try:
                if self.use_rvc and self.rvc_converter:
                    self._speak_with_rvc(text)
                else:
                    self._speak_direct(text)

            except Exception as e:
                print(f"❌ TTS Error: {e}")
                traceback.print_exc()
            finally:
                self.is_speaking = False
                print("✅ TTS: Завершено")

        self._current_thread = threading.Thread(target=_process, daemon=True)
        self._current_thread.start()

    def _speak_with_rvc(self, text):
        """Озвучка с RVC конвертацией"""
        try:
            # Создаем временные файлы
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_input:
                temp_input_path = temp_input.name

            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_output:
                temp_output_path = temp_output.name

            # Шаг 1: Генерация базовой речи
            print("🔊 Генерирую базовую речь...")
            self._generate_base_speech(text, temp_input_path)

            # Шаг 2: Конвертация через RVC
            print("🔄 Конвертирую голос через RVC...")
            converted_path = self.rvc_converter.convert_audio(
                input_audio_path=temp_input_path,
                output_path=temp_output_path,
                f0_up_key=0
            )

            if converted_path and os.path.exists(converted_path):
                # Шаг 3: Воспроизведение результата
                print("▶️ Воспроизвожу результат...")
                self._play_audio(converted_path)
                print("🎉 RVC конвертация завершена!")
            else:
                print("❌ Конвертация не удалась, воспроизвожу оригинал")
                self._play_audio(temp_input_path)

            # Очистка временных файлов
            self._cleanup_files([temp_input_path, temp_output_path])

        except Exception as e:
            print(f"❌ RVC обработка не удалась: {e}")
            self._speak_direct(text)

    def _speak_direct(self, text):
        """Прямая озвучка без RVC"""
        import pyttsx3

        engine = pyttsx3.init()
        engine.setProperty('rate', 180)
        engine.setProperty('volume', 1.0)

        voices = engine.getProperty('voices')
        if voices and len(voices) > self.voice_index:
            engine.setProperty('voice', voices[self.voice_index].id)

        engine.say(text)
        engine.runAndWait()

    def _generate_base_speech(self, text, output_path):
        """Генерация базовой речи для RVC"""
        import pyttsx3

        engine = pyttsx3.init()
        engine.setProperty('rate', 180)
        engine.setProperty('volume', 1.0)

        voices = engine.getProperty('voices')
        if voices and len(voices) > self.voice_index:
            engine.setProperty('voice', voices[self.voice_index].id)

        engine.save_to_file(text, output_path)
        engine.runAndWait()

    def _play_audio(self, audio_path):
        """Воспроизведение аудио файла"""
        try:
            import pygame

            if not pygame.mixer.get_init():
                pygame.mixer.init()

            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                threading.Event().wait(0.1)

        except ImportError:
            self._play_audio_system(audio_path)

    def _play_audio_system(self, audio_path):
        """Воспроизведение через системный плеер"""
        import subprocess
        import platform

        system = platform.system().lower()
        try:
            if system == 'windows':
                import winsound
                winsound.PlaySound(audio_path, winsound.SND_FILENAME)
            elif system == 'darwin':
                subprocess.run(['afplay', audio_path], check=True)
            else:
                subprocess.run(['aplay', audio_path], check=True)
        except Exception as e:
            print(f"❌ Ошибка воспроизведения: {e}")

    def _cleanup_files(self, file_paths):
        """Очистка временных файлов"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"⚠️ Не удалось удалить файл {file_path}: {e}")

    def stop(self):
        """Остановить речь"""
        self.is_speaking = False
        print("⏹️ TTS: Остановлено")

        try:
            import pygame
            pygame.mixer.music.stop()
        except:
            pass

TTSEngine = SimpleRVCTTSEngine