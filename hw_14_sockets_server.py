import socket
from threading import Event, Thread
from typing import Tuple

import keyboard


def server(host: str, port: int, run: Event, log_filename_prefix: str):
    """Runs a server accepting multiple connections.
    Server and clients shutdown by specified event clear."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.settimeout(3)
        server_sock.bind((host, port))
        server_sock.listen()

        while run.is_set():
            try:
                client, addr = server_sock.accept()
            except socket.timeout:
                continue

            Thread(target=work_with_one_client, args=(client, addr, run, log_filename_prefix)).start()


def work_with_one_client(client_sock: socket.socket, client_addr: Tuple[str, int], run: Event, log_fn_prefix: str):
    """Receives and saves data to file.
    Log file name consists of port and specified prefix."""

    with client_sock:
        print(f'Server: {client_addr} connected')

        with open(f'{log_fn_prefix}_{client_addr[1]}.txt', 'a+') as f:
            while run.is_set():
                data = client_sock.recv(1024).decode("utf-8")
                print(f'Server: Recvd: {data}')

                f.write(f'{data}\n')


if __name__ == '__main__':
    HOST = '127.0.0.1'
    PORT = 65432
    keep_running = Event()
    keep_running.set()

    Thread(target=server, args=(HOST, PORT, keep_running, 'sensor_log')).start()

    keyboard.wait('Esc')
    keep_running.clear()
