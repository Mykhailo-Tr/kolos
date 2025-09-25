# fake_weight_reader.py

import threading
import time

class FakeWeightReader:
    def __init__(self):
        self.latest_weight = 100
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join()

    def set_weight(self, value: float):
        """Ручне встановлення ваги"""
        self.latest_weight = float(value)

    def _run(self):
        # Емуляція "живого" пристрою: просто крутиться в циклі
        while not self._stop.is_set():
            # нічого не робимо, але можна додати sleep
            time.sleep(0.2)
