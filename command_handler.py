import shlex
import subprocess
import os

class CommandHandler:
    def __init__(self, commands_map, avatar_actions, tts_engine, avatar):
        self.commands = {k.lower(): v for k, v in commands_map.items()}
        self.avatar_actions = {k.lower(): v for k, v in avatar_actions.items()}
        self.tts = tts_engine
        self.avatar = avatar
        print(f"🎯 CommandHandler: {len(self.avatar_actions)} avatar actions loaded")

    def handle(self, text):
        text = text.lower().strip()
        print(f"🔍 Processing: '{text}'")

        # 1. Перевірка на аватар-команди (спочатку, бо вони швидші)
        for phrase, action in self.avatar_actions.items():
            if phrase in text:
                print(f"🎭 Found avatar action: {phrase}")

                expr = action.get("expression")
                motion = action.get("motion")
                speech = action.get("speak")

                # Обробка виразу
                if expr:
                    print(f"  → Sending expression: {expr}")
                    self.avatar.send_expression(expr)

                # Обробка анімації
                if motion:
                    print(f"  → Sending motion: {motion}")
                    self.avatar.send_motion(motion)

                # Обробка мови
                if speech:
                    print(f"  → Speaking: {speech}")
                    self.tts.speak(speech)

                return True

        # 2. Перевірка на програмні команди
        for phrase, info in self.commands.items():
            if phrase in text:
                print(f"🚀 Found program command: {phrase}")
                self._run_program(info)
                self.tts.speak(f"Everything for you, master")
                return True

        print(f"❌ No command found for: '{text}'")
        return False

    def _run_program(self, info):
        prog = info.get("program")
        args = info.get("args", [])
        try:
            if prog.lower().endswith(".exe") or os.path.isabs(prog):
                subprocess.Popen([prog] + args, shell=False)
            else:
                try:
                    os.startfile(prog)
                except Exception:
                    subprocess.Popen([prog] + args, shell=True)
        except Exception as e:
            print("Error launching:", e)