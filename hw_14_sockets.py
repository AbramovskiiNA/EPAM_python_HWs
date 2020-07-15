import datetime
import socket
from queue import LifoQueue
from threading import Event, Thread
from typing import Callable

import keyboard
import psutil


class SensorMonitor:
    """Performs threaded data acquisition from specified sensor."""

    def __init__(self, source: Callable, interval: int):
        self.source = source
        self.interval = interval

        self.data = LifoQueue()
        self.keep_acq = Event()
        self.keep_acq.set()

    def start_collect(self):
        Thread(target=self._continuous_acquisition, args=(self.source, self.interval)).start()

    def _continuous_acquisition(self, source: Callable, interval: int):
        while self.keep_acq.is_set():
            self.data.put(source(interval))

    def get_current_state(self) -> str:
        return f'{datetime.datetime.now()}\tcpu_usage\t{self.data.get()}'

    def cleanup(self):
        with self.data.mutex:
            self.data.queue.clear()

    def stop_collect(self):
        self.keep_acq.clear()


def server(run: Event, host: str, port: int, log_fp: str):
    """Runs server connected to single client.
    Receives and saves data to specified file.
    Shutdown by specified event clear."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.bind((host, port))
        server_sock.listen()

        client_sock, addr = server_sock.accept()
        with client_sock:
            print(f'Server: {addr} connected')

            with open(log_fp, 'a+') as f:
                while run.is_set():
                    data = f'{client_sock.recv(1024).decode("utf-8")}\n'
                    print(f'Server: Recvd: {data}')

                    f.write(data)


def client(run: Event, host: str, port: int, monitor: SensorMonitor):
    """Client collecting data from specified sensor monitor.
    Sends data to server.
    Closing by specified event clear."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_sock:
        client_sock.connect((host, port))

        monitor.start_collect()
        while run.is_set():
            data = monitor.get_current_state()
            client_sock.sendall(data.encode('utf-8'))
            print(f'Client: Sent: {data}')
        monitor.stop_collect()


if __name__ == '__main__':
    sm = SensorMonitor(psutil.cpu_percent, 2)
    HOST = '127.0.0.1'
    PORT = 65432
    keep_running = Event()
    keep_running.set()

    Thread(target=server, args=(keep_running, HOST, PORT, 'sensor_log.txt')).start()
    Thread(target=client, args=(keep_running, HOST, PORT, sm)).start()

    keyboard.wait('Esc')
    keep_running.clear()
