# mkbigfifo

mkbigfifo is a program that supplements mkfifo by allowing to create named
pipes that have by default the maximum allowed buffer size.

## Introduction
`mkfifo` creates named pipes on the operating system. These pipes default 
to the default pipe size. On recent versions of the linux kernel this is 
64K. When large volumes of data are processed and piped into another program 
the pipe size can be limiting. 

For example `program_a my_big_file | program_b -o result_file`. If program_b
momentarily stops input processing while it writes a chunk to the result file
this will block program_a at the moment the pipe buffer is full. By using a 
bigger pipe buffer these moments where the pipe buffer is full will occur less 
frequently.

## Usage
Since pipe size can only be modified by *running* programs `mkbigfifo` must
run until all the  programs using the named pipes are finished.
Mkbigfifo will exit gracefully and remove the pipes after it receives a 
SIGINT (ctrl-c) or SIGTERM signal. It can be used in scripts like this:

```bash 
mkbigfifo fifo1 fifo2 &
FIFO_PID=$!
program1 -o fifo1 -i /some/input &
program2 -o fifo2 -i fifo1 &
program3 -i fifo2 -o /some/output
kill $FIFO_PID
```

Alternatively you can create the pipes in a separate terminal window:
`mkbigfifo mypipe`. And then terminate with ctrl-c when done.

### CLI
```
usage: mkbigfifo [-h] [-s SIZE] [-v] [-q] FIFO [FIFO ...]

positional arguments:
  FIFO                  One or multiple named pipes to create.

optional arguments:
  -h, --help            show this help message and exit
  -s SIZE, --size SIZE  Size in bytes for the fifo files. Default is the
                        maximum user-allowed pipe size on the system. On this
                        system that is 1048576 bytes.
  -v, --verbose         Increase verbosity. Multiple flags allowed.
  -q, --quiet           Decrease verbosity. Multiple flags allowed.
```
## Why not mkfifo?
Unfortunately mkfifo can NOT be used to set the size in advance. The size is 
determined by the kernel and can only set by a program that has opened the 
fifo.

[Solutions have been presented on stackoverflow](
https://unix.stackexchange.com/a/439438)
but these require the use of `fcntl` kernel calls. A working example in python
can be found [here](
https://www.golinuxhub.com/2018/05/how-to-view-and-increase-default-pipe-size-buffer/).
Mkbigfifo was made to provide an easy interface to these solutions.

## Acknowledgements

Thanks to [Stéphane Chazelas](
https://unix.stackexchange.com/users/22565/st%c3%a9phane-chazelas) for 
outlining how to increase the size of a named pipe.

Huge thanks to [golinuxhub](https://www.golinuxhub.com/) for creating the 
python example. This was the basis of this program.

Thanks to [Mayank Jaiswal](https://stackoverflow.com/users/578989/mayank-jaiswal)
for providing an [example how to process signals in python](
https://stackoverflow.com/a/31464349). This example was used to properly handle
SIGINT and SIGTERM signals in this program.