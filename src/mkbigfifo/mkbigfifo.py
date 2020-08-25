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
import contextlib
import fcntl
import logging
import os
import queue
import signal
import threading
import time
from pathlib import Path
from typing import Iterable

F_SET_PIPE_SZ = 1031
F_GET_PIPE_SZ = 1032

PAGE_SIZE = os.sysconf("SC_PAGESIZE")
MAX_PIPE_SIZE = int(Path("/proc/sys/fs/pipe-max-size").read_text())


def argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("FIFO", nargs="+",
                        help="One or multiple named pipes to create.")
    parser.add_argument("-s", "--size", type=int, default=MAX_PIPE_SIZE,
                        help=f"Size in bytes for the fifo files. Default is "
                             f"the maximum user-allowed pipe size on the "
                             f"system. On this system that is "
                             f"{MAX_PIPE_SIZE} bytes.")
    parser.add_argument("-v", "--verbose", action="count", default=0,
                        help="Increase verbosity. Multiple flags allowed.")
    parser.add_argument("-q", "--quiet", action="count", default=0,
                        help="Decrease verbosity. Multiple flags allowed.")
    return parser


def get_pipe_size(fd: int):
    return fcntl.fcntl(fd, F_GET_PIPE_SZ)


def get_fifo_size(path: str):
    fd = os.open(path, os.O_RDONLY)
    return get_pipe_size(fd)


class BigFIFO:
    def __init__(self, path: str, pipe_size: int = MAX_PIPE_SIZE):
        self.path = path

        if pipe_size % PAGE_SIZE != 0:
            logging.warning(f"{pipe_size} is not a multiple of the page size: "
                            f"{PAGE_SIZE}. It will be rounded up automatically"
                            f" to {(pipe_size // PAGE_SIZE + 1) * PAGE_SIZE}.")
        if pipe_size > MAX_PIPE_SIZE:
            # Raise a ValueError here. Otherwise fcntl will raise a
            # non-descriptive permission error.
            raise ValueError(
                f"{pipe_size} is bigger than maximum of {MAX_PIPE_SIZE}")

        logging.info(f"Create '{self.path}' with size {pipe_size}")
        os.mkfifo(self.path)
        self.fd = os.open(self.path, os.O_RDWR)
        fcntl.fcntl(self.fd, F_SET_PIPE_SZ, pipe_size)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        os.close(self.fd)
        os.remove(self.path)

    def wait(self, interval: int = 1, delta_ns: int = 1 * 10 ** 9):
        """Waits until the pipe is not used anymore."""
        signal_catcher = SignalCatcher((signal.SIGTERM, signal.SIGINT))
        while not signal_catcher.catched:
            if time.time_ns() - os.stat(self.path).st_atime_ns > delta_ns:
                return
            time.sleep(interval)
        logging.debug(f"Closing fifo file {self.path} after receiving signal "
                      f"{signal_catcher.received_signal}")

    def size(self):
        """Returns the size of the pipe"""
        return get_pipe_size(self.fd)


class SignalCatcher():
    """
    Catch a signal and store a signal number. Useful for usage in while loops.
    https://stackoverflow.com/a/31464349
    """
    def __init__(self, signals: Iterable[int]):
        self.catched = False
        self.received_signal = None
        for sign in signals:
            signal.signal(sign, self._handle_signal)

    def _handle_signal(self, signum, frame):
        self.received_signal = signum
        self.catched = True


def create_fifo_files_daemon(paths: Iterable[str],
                             size: int = MAX_PIPE_SIZE):
    with contextlib.ExitStack() as stack:
        fifos = [stack.enter_context(BigFIFO(path, size)) for path in paths]
        threads = [threading.Thread(target=fifo.wait()) for fifo in fifos]
        time.sleep(15)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()


def main():
    args = argument_parser().parse_args()
    logger = logging.getLogger()
    # The lower the level the more verbose.
    logger.setLevel(logging.WARNING + (args.quiet - args.verbose) * 10)

    create_fifo_files_daemon(args.FIFO, args.size)


if __name__ == "__main__":  # pragma: no cover
    main()
