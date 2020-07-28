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

import os
import signal
import subprocess
import time
from pathlib import Path

from mkbigfifo import BigFIFO, MAX_PIPE_SIZE, get_fifo_size

import pytest


def test_mkbigfifo_default(caplog):
    with BigFIFO("mypipe") as mypipe:
        assert mypipe.size() == MAX_PIPE_SIZE
    assert not os.path.exists(mypipe.path)
    # No messages by default.
    assert len(caplog.messages) == 0


def test_mkbigfifo_value():
    with BigFIFO("mypipe", 4096) as mypipe:
        assert mypipe.size() == 4096
    assert not os.path.exists(mypipe.path)


def test_mkbigfifo_warning(caplog):
    with BigFIFO("mypipe", 128) as mypipe:
        assert mypipe.size() == 4096
    assert not os.path.exists(mypipe.path)
    assert caplog.messages[0] == ("128 is not a multiple of 4096. It will be "
                                  "rounded up automatically to 4096.")


def test_bigfifo_too_big():
    with pytest.raises(ValueError) as error:
        BigFIFO("mypipe", MAX_PIPE_SIZE + 1)
    error.match("is bigger than maximum")


@pytest.mark.parametrize("sign", [signal.SIGINT, signal.SIGTERM])
def test_program(sign):
    args = ("mkbigfifo", "-s", "4096", "pipe1", "pipe2", "-vvvvv")
    mkbigfifo_process = subprocess.Popen(args)
    time.sleep(0.1)  # Sleep a bit to allow creating files.
    assert Path("pipe1").exists()
    assert Path("pipe2").exists()
    assert get_fifo_size("pipe1") == 4096
    assert get_fifo_size("pipe2") == 4096
    mkbigfifo_process.send_signal(sign)
    mkbigfifo_process.wait()
    exit_code = mkbigfifo_process.poll()
    assert not Path("pipe1").exists()
    assert not Path("pipe2").exists()
    assert exit_code == 0
