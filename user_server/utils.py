import os
import subprocess
import signal
import time
from time import sleep
from threading import Timer

PROJECT_DIR = os.path.join(os.getcwd(), "..")
DATA_DIR = os.path.join(PROJECT_DIR, "user_server/data")


class LogHandler():
    def __init__(self, file_name):
        self.fd = open(file_name, 'w', encoding='utf-8')

    def __del__(self):
        self.fd.close()

    def info(self, sth):
        format_time = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        self.fd.write(f"[{format_time} INFO] {sth}\n")

    def warn(self, sth):
        format_time = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        self.fd.write(f"[{format_time} WARN] {sth}\n")

    def error(self, sth):
        format_time = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        self.fd.write(f"[{format_time} ERROR] {sth}\n")


def exec_bash(cmd, wait=True, timeout=None):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                         encoding='utf-8', preexec_fn=os.setsid)
    if not wait:
        return
    if timeout:
        timeout = int(timeout)

        def func(p):
            try:
                p.terminate()
                p.wait()
                os.killpg(p.pid, signal.SIGTERM)
            except:
                pass
        t = Timer(timeout, func, [p])
        t.start()
    p.wait()
    return p.stdout.read().split('\n')[:-1]
