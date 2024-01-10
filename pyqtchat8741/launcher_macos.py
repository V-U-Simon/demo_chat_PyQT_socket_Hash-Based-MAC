"""
It is a launcher for starting subprocesses for server and clients of two types: senders and listeners.
for more information:
https://stackoverflow.com/questions/67348716/kill-process-do-not-kill-the-subprocess-and-do-not-close-a-terminal-window
"""

import os
import signal
import subprocess
import sys
from time import sleep

PYTHON_PATH = sys.executable
BASE_PATH = os.path.dirname(os.path.abspath(__file__))


def get_subprocess(command):
    sleep(0.2)
    args = [command]
    return subprocess.Popen(args, preexec_fn=os.setpgrp)


def main():
    process = []
    while True:
        TEXT_FOR_INPUT = "Выберите действие: q - выход, s - запустить сервер и клиенты, x - закрыть все окна: "
        action = input(TEXT_FOR_INPUT)

        if action == "q":
            break
        elif action == "s":
            process.append(get_subprocess("pyqtchat8741_server"))
            sleep(1)

            for i in range(2):
                process.append(get_subprocess(f"pyqtchat8741_client"))

        elif action == "x":
            while process:
                victim = process.pop()
                victim.terminate()  # Завершаем процесс
                victim.wait()  # Ожидаем завершения процесса


if __name__ == "__main__":
    main()
