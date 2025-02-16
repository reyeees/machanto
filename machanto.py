from sys import executable as PYTHON
from os import system
from importlib.util import find_spec

# installing packages if user is 怠け者
missing = []
for package in ("requests", "tqdm"):
    if find_spec(package) is None:
        missing.append(package)
if missing != []:
    system(f"\"{PYTHON}\" -m pip install {' '.join(missing)}")
del PYTHON, system, find_spec, missing

# actual code starts here.

from argparse import ArgumentParser
from lib.downloader import FileDownloader

parser = ArgumentParser(description = "Multi-threaded file downloader.")
parser.add_argument("url", help = "File URL to download")
parser.add_argument("-o", "--output", default = "", help = "Output file path")
parser.add_argument("-t", "--threads", type = int, default = 4, help = "Number of download threads")

if __name__ == "__main__":
    args = parser.parse_args()
    downloader = FileDownloader(args.url, args.output, args.threads)
    downloader.download()
