import shlex
import subprocess
import os

class CommandHandler:
    def __init__(self, commands_config, tts_engine, avatar_client):
        # Тепер ми приймаємо лише один словник з усіма командами
        self.commands = {k.lower(): v for k, v in commands_config.items()}
        self.tts = tts_engine
        self.avatar = avatar_client
        print(f"🎯 CommandHandler: {len(self.commands)} total commands loaded.")

    def handle(self, text: str) -> bool:
        """
        Обробляє вхідний текст, шукає відповідну команду та виконує всі пов'язані з нею дії.
        """
        text = text.lower().strip()

        # Єдиний цикл для всіх команд
        for phrase, actions in self.commands.items():
            if phrase in text:
                print(f"✅ Found command: '{phrase}'")

                # Отримуємо всі можливі дії з конфігу
                program_to_run = actions.get("program")
                expression_to_show = actions.get("expression")
                motion_to_play = actions.get("motion")
                text_to_speak = actions.get("speak")

                # 1. Запуск програми
                if program_to_run:
                    print(f"  → Running program: {program_to_run}")
                    self._run_program(program_to_run)

                # 2. Надсилання виразу аватару
                if expression_to_show:
                    print(f"  → Sending expression: {expression_to_show}")
                    self.avatar.send_expression(expression_to_show)

                # 3. Надсилання анімації аватару
                if motion_to_play:
                    print(f"  → Sending motion: {motion_to_play}")
                    self.avatar.send_motion(motion_to_play)

                # 4. Озвучення тексту
                if text_to_speak:
                    print(f"  → Speaking: '{text_to_speak}'")
                    self.tts.speak(text_to_speak)

                return True # Команду знайдено та оброблено, виходимо

        # Якщо жодна команда не знайдена, повертаємо False
        # Це дозволить передати текст до LLM у main.py
        return False

    def _run_program(self, program_path):
        """Запускає зовнішню програму."""
        try:
            # Popen є неблокуючим, що ідеально для асистента
            subprocess.Popen([program_path], shell=False)
        except Exception as e:
            print(f"❌ Error launching program '{program_path}': {e}")