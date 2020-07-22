import argparse
import os.path
import urllib.request
from http.client import HTTPResponse
from pathlib import Path
from queue import Queue
from threading import Thread
from time import perf_counter
from typing import Tuple
from urllib.error import URLError, HTTPError

from PIL import Image, UnidentifiedImageError


def download_image(urls_q: Queue, resps_q: Queue):
    """Takes (position, url) from urls queue
    and puts (position, response) to responses queue."""

    while not urls_q.empty():
        pos, url = urls_q.get()

        try:
            resp = urllib.request.urlopen(url)
        except (URLError, HTTPError):
            resp = None

        resps_q.put((pos, resp))
        # print(f'{current_thread().name}:\tImage {pos} downloaded.')


def process_image(tup: Tuple[int, HTTPResponse], thumbnail_size, dir_path: str) -> Image:
    """Creates image from response and reads content size.
    Saves image thumbnail."""

    pos, resp = tup

    if not resp:
        return

    try:
        im = Image.open(resp).convert('RGB')
    except UnidentifiedImageError:
        return

    im.thumbnail(thumbnail_size)

    size_b = int(resp.info()['Content-Length'])
    im.save(os.path.join(dir_path, f'{pos:05}.jpeg'))
    # print(f'{current_thread().name}:\tImage {pos} saved.')
    print(f'Image {pos} processed.')

    return size_b


def main(urllist_fn: str, thumbnails_dir: str, threads_count: int, thumbnails_size: [Tuple[int, int], Tuple[int, ...]]):
    """Creates thumbnalis path if not existed.
    Takes urls and puts them into queue with their position.

    Starts downloading threads.
    Keeps image processing and statistics acquisition, until all threads are finished and response queue is empty.

    Measures whole process time."""

    t_start = perf_counter()

    files_downloaded = 0
    bytes_downloaded = 0
    requests_failed = 0

    urls_queue = Queue()
    resps_queue = Queue()

    Path(thumbnails_dir).mkdir(parents=True, exist_ok=True)

    with open(urllist_fn) as f:
        urllist = f.readlines()
    for position, img_url in enumerate(urllist):
        urls_queue.put((position, img_url))

    downl_thrs = [Thread(target=download_image, args=(urls_queue, resps_queue)) for _ in range(threads_count)]
    _ = [thr.start() for thr in downl_thrs]

    while any([thr.is_alive() for thr in downl_thrs]) or not resps_queue.empty():
        b_downloaded = process_image(resps_queue.get(), thumbnails_size, thumbnails_dir)

        if b_downloaded:
            files_downloaded += 1
            bytes_downloaded += b_downloaded
        else:
            requests_failed += 1

    print(f'\nFiles downloaded:\t{files_downloaded}\nBytes downloaded:\t{bytes_downloaded:_}\n'
          f'Requests failed:\t{requests_failed}\nTotal time, sec:\t{perf_counter() - t_start:.4}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('urllist_filename')
    parser.add_argument('--dir', default=os.getcwd())
    parser.add_argument('--threads', default=1)
    parser.add_argument('--size', default='100x100')
    args = parser.parse_args()

    size = tuple(map(int, args.size.split('x')))
    urllist_filename = args.urllist_filename

    if os.path.isfile(urllist_filename):
        main(urllist_filename, args.dir, int(args.threads), size)
    else:
        print('URL List File not found.\nExiting.')
