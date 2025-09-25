
import threading
import serial
import time

class WeightReader:
    def __init__(self, port="/dev/ttyUSB0", baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.latest_weight = None
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join()

    def _parse_line(self, line: bytes):
        """
        Парсити рядок від ваги, наприклад: b'WG00012.34kg3D\r\n'
        У документації формат 15 байт: ‘W’ + ‘G’/’N’ + число + ‘kg’ + checksum + \r\n :contentReference[oaicite:2]{index=2}
        """
        try:
            text = line.decode("ascii", errors="ignore").strip()
            # приклад: "WG00012.34kg3D"
            if not text.startswith("W"):
                return None
            # просто знайдемо число між другим символом і "kg"
            idx = text.find("kg")
            if idx < 0:
                return None
            num = text[2:idx]
            return float(num)
        except Exception:
            return None

    def _run(self):
        try:
            ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        except Exception as e:
            print("Cannot open serial port:", e)
            return

        while not self._stop.is_set():
            try:
                line = ser.readline()  # читає до \n
            except Exception as e:
                print("Serial read error:", e)
                break
            if not line:
                continue
            w = self._parse_line(line)
            if w is not None:
                self.latest_weight = w
            # невелика пауза, щоб не навантажувати порт
            time.sleep(0.1)

        ser.close()
