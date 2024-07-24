import os
import re
import subprocess
import tempfile
from itertools import groupby
from pathlib import Path


def convert(vtt):
    def is_timestamp(line):
        return re.search(
            r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3} align:start position:0%',
            line,
        )

    lines = vtt.splitlines()
    for i in range(len(lines)):
        if is_timestamp(lines[i]):
            break

    raw = []
    for l in lines[i:]:
        if is_timestamp(l):
            continue
        else:
            l = l.strip()
            if l:
                raw.append(re.sub(r'(<.*?>)', '', l) + '\n')

    return ''.join(x[0] for x in groupby(raw))


def get_subtitles(url):
    with tempfile.TemporaryDirectory() as d:
        os.chdir(d)
        subprocess.run(
            [
                'yt-dlp',
                url,
                '--skip-download',
                '--write-sub',
                '--write-auto-sub',
                '--sub-lang',
                'en.*',
            ],
            check=True,
        )
        return convert(next(Path(d).glob('*.vtt')).read_text())


# print(get_subtitles('https://www.youtube.com/watch?v=Iow92wFKp-w'))
