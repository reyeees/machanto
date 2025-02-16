from pathlib import Path
from time import sleep


class Utils:
    def __init__(self) -> None:
        pass

    @staticmethod
    def countdown(count: int = 5) -> None:
        for x in range(count, 0, -1):
            print(x, end = "\r")
            sleep(1)
        print(" ")

    @staticmethod
    def exists(filename: str, filesize: int = None) -> bool:
        file = Path(filename)
        if filesize is None or not file.exists():
            return file.exists()

        not_empty = file.stat().st_size == filesize
        return file.exists() and not_empty
    
    @staticmethod
    def get_size(filename: str) -> int:
        file = Path(filename)
        if file.exists():
            return file.stat().st_size
        return 0

    @staticmethod
    def split_chunks(filesize: int, threads: int) -> list:
        chunk_size = filesize // threads
        return [
            (i * chunk_size, (i + 1) * chunk_size - 1 if i < threads - 1 else filesize - 1, i)
            for i in range(threads)
        ]

    @staticmethod
    def get_range(init_pos: int, start: int, end: int) -> dict[str, str]:
        return {"Range": f"bytes={start + init_pos}-{end}"}
