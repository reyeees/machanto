from sys import exit
from signal import SIGINT, signal
from os import makedirs, path, remove, rmdir
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Event

from requests import Session
from .core.chunks import ChunkDownloader
from .core.utils import Utils

STOP_FLAG = Event()
def signal_listener(sig, frame) -> None:
    print(f"\nSignal catched, interrupting everything.")
    STOP_FLAG.set()
    exit(0)
signal(SIGINT, signal_listener)


class FileDownloader:
    def __init__(self, url: str, output_file: str, num_threads: int = 4):
        self.url: str = url
        self.output_file: str = self._get_output_file(output_file)
        self.num_threads: int = num_threads
        self.output_dir: str = "temp_chunks"

        self.session = Session()
        self.utils = Utils
        self.stop_flag = STOP_FLAG

    def _get_output_file(self, output: str) -> str:
        if output == "":
            return self.url.split('/')[-1]
        return output

    def _prepare_download(self):
        response = self.session.head(self.url, timeout = 5)
        if 'content-length' not in response.headers:
            raise Exception("Unable to determine file size. "
                            "Server doesn't support range requests.")
        
        self.file_size = int(response.headers['content-length'])

        if self.utils.exists(self.output_file, self.file_size):
            print(f"{self.output_file} already downloaded.")
            return True

        makedirs(self.output_dir, exist_ok = True)
        return False

    def download(self):
        if self._prepare_download():
            return

        chunks = self.utils.split_chunks(self.file_size, self.num_threads)
        futures = []
        
        with ThreadPoolExecutor(max_workers = self.num_threads) as executor:
            for start, end, part_num in chunks:
                if self.stop_flag.is_set():
                    executor.shutdown(wait = False, cancel_futures = True)
                future = executor.submit(
                    ChunkDownloader(
                        self.url, start, end, part_num, 
                        self.output_dir, self.output_file, 
                        self.stop_flag, self.session, 3).download_chunk
                )
                futures.append(future)

            for future in as_completed(futures):
                if future.result() is None:
                    self.stop_flag.set()
                    print("Some chunks failed.")
                    return
        
        self._merge_chunks()

    def _merge_chunks(self):
        if self.stop_flag.is_set():
            print("Download was interrupted. Partial files remain.")
            return

        with open(self.output_file, 'wb') as output_file:
            for i in range(self.num_threads):
                chunk_file = path.join(self.output_dir, f"part_{i}_{self.output_file.replace('.', '_')}.tmp")
                if path.exists(chunk_file):
                    with open(chunk_file, 'rb') as chunk:
                        output_file.write(chunk.read())
                    remove(chunk_file)

        rmdir(self.output_dir)
        print(f"{self.output_file} download complete!")
