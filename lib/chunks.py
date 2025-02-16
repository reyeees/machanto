from os import path
from requests import Session
from requests.exceptions import RequestException
from tqdm import tqdm

from threading import Event
from lib.utils import Utils


class ChunkDownloader:
    def __init__(self, url: str, start: int, end: int, part_num: int, 
                 output_dir: str, filename: str, stop_flag: Event, 
                 session: Session, max_retries: int = 3):
        self.filename = filename.replace('.', '_')
        self.filename = f"part_{part_num}_{self.filename}.tmp"
        self.url = url
        
        self.start = start
        self.end = end
        self.total_size = self.end - self.start + 1
        self.part_num = part_num
        self.max_retries = max_retries
        self.stop_flag = stop_flag
        
        self.output_dir = output_dir
        self.chunk_file = path.join(output_dir, self.filename)

        self.session: Session = session
        self.utils = Utils
        self.progress_bar: tqdm = None

    def download_chunk(self):
        init_pos = self.utils.get_size(self.chunk_file)
        headers = self.utils.get_range(init_pos, self.start, self.end)

        if init_pos >= self.total_size:
            print(f"Chunk {self.part_num} already downloaded.")
            return self.chunk_file
        
        self.progress_bar = tqdm(
            total = self.total_size,
            initial = init_pos,
            unit = 'B',
            unit_scale = True,
            desc = f"Chunk {self.part_num}",
            ascii = False,
            dynamic_ncols = True
        )

        retries = 0
        while retries < self.max_retries:
            try:
                with self.session.get(self.url, headers = headers, 
                                      stream = True, timeout = 10) as response:
                    if response.status_code not in (200, 206):  # 206: Partial Content
                        raise Exception(f"Failed to download chunk "
                                        "{self.part_num} {self.filename}")
                    
                    with open(self.chunk_file, 'ab') as file:
                        for chunk in response.iter_content(1024):
                            if self.stop_flag.is_set():
                                print(f"{self.part_num} - Catched interrupt signal")
                                return None
                            if chunk:
                                file.write(chunk)
                                self.progress_bar.update(len(chunk))
                    self.progress_bar.close()
                return self.chunk_file
            except RequestException as e:
                retries += 1
                init_pos = self.utils.get_size(self.chunk_file)
                headers = self.utils.get_range(init_pos, self.start, self.end)

                print(f"  ... Network error - part {self.part_num}. "
                      f"Retrying ({retries}/{self.max_retries})", end = "\r")
                self.utils.countdown(5)
        return None
