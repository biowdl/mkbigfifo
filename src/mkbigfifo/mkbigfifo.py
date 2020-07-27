#!/usr/bin/env python3

# Copyright (c) 2020 Leiden University Medical Center
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import fcntl
import os
from pathlib import Path
from typing import Optional

F_SET_PIPE_SZ = 1031
F_GET_PIPE_SZ = 1032
MAX_PIPE_SIZE = int(Path("/proc/sys/fs/pipe-max-size").read_text())


def argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("FIFO", nargs="+", help="FIFO files to create")
    parser.add_argument("-s", "--size",
                        help=f"Size in bytes for the fifo files. Default is "
                             f"the maximum user-allowed pipe size on the "
                             f"system. On this system that is "
                             f"{MAX_PIPE_SIZE} bytes.")
    return parser


class BigFIFO:
    def __init__(self, path: str, pipe_size: int = MAX_PIPE_SIZE):
        self.path = path
        self.pipe_size = pipe_size
        self.fd: Optional[int] = None

    def __enter__(self):
        os.mkfifo(self.path)
        self.fd = os.open(self.path, os.O_RDWR | os.O_APPEND)
        fcntl.fcntl(self.fd, F_SET_PIPE_SZ, self.pipe_size)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.close(self.fd)
        os.remove(self.path)

    def size(self):
        """Returns the size of the pipe"""
        return fcntl.fcntl(self.fd, F_GET_PIPE_SZ)
