#!/usr/bin/env python3

import os
import sys
import time
import RPi.GPIO as GPIO
from clock_nanosleep import (
        CLOCK_REALTIME,
        CLOCK_TAI,
        TIMER_ABSTIME,
        TIME_ERROR,
        clock_gettime_ts,
        clock_nanosleep_ts,
        timespec,
        ntp_adjtime,
        )

def sq(s):
    """Safely shell-quote the argument"""
    return "'" + s.replace("'", "'\\''") + "'"

class Tee:
    def __init__(self, *sub_fds):
        self.sub_fds = sub_fds

    def write(self, buf):
        for s in self.sub_fds:
            s.write(buf)
        return len(buf)

    def flush(self):
        return self.sub_fds[0].flush()

class DatedFile:
    def __init__(self, timestamp, format):
        self._format = format
        self._timestamp = None
        self._filename = None
        self._file = None
        self.timestamp = timestamp

    @property
    def filename(self):
        return self._filename

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value):
        filename = time.strftime(self._format, time.gmtime(value))
        if filename != self._filename:
            if self._filename is not None:
                qf = sq(self._filename)
                os.system(f"(git add {qf} && git commit -m'Add {qf}' {qf})&")
            self._filename = filename
            if self._file is not None:
                self._file.close()
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            self._file = open(filename, 'at', encoding='utf-8')
            if self._file.tell():
                self._file.write('\n')

    def write(self, buf):
        return self._file.write(buf)

    def flush(self):
        return self._file.flush()

def main():
    GPIO.setmode(GPIO.BOARD)
    PIN = 3
    GPIO.setup([PIN], GPIO.IN)

    if sudo_gid := os.environ.get('SUDO_GID'):
        print(f"Setting GID to {sudo_gid}", file=sys.stderr)
        os.setgid(int(os.environ['SUDO_GID']))
    if sudo_uid := os.environ.get('SUDO_UID'):
        print(f"Setting UID to {sudo_uid}", file=sys.stderr)
        os.setuid(int(os.environ['SUDO_UID']))

    if ntp_adjtime()[0] == TIME_ERROR:
        print("Waiting for NTP sync", end="", file=sys.stderr)
        sys.stderr.flush()
        while ntp_adjtime()[0] == TIME_ERROR:
            time.sleep(1)
            print(end=".", file=sys.stderr)
            sys.stderr.flush()
        print(file=sys.stderr)

    now = clock_gettime_ts(CLOCK_TAI)
    deadline = timespec(now.tv_sec + 1, 0)
    logfile = DatedFile(deadline.tv_sec, "data/%Y/%m-%d.txt")
    sys.stdout = Tee(sys.stdout, logfile)

    end = ""
    try:
        while True:
            clock_nanosleep_ts(CLOCK_TAI, TIMER_ABSTIME, deadline)
            st = GPIO.input(PIN)
            i = deadline.tv_nsec // 10_000_000
            if deadline.tv_nsec == 0:
                print(end=end)
                end="\n"
                g = time.gmtime(deadline.tv_sec)
                print(end=f'{time.strftime("%Y-%m-%d %H:%M:%S TAI ", g)}')
                logfile.timestamp = deadline.tv_sec
            if i in [20, 50, 80]:
                print(end="|")
            print(end="#" if st else "_")
            sys.stdout.flush()
            deadline.tv_nsec += 20_000_000
            if deadline.tv_nsec >= 1_000_000_000:
                deadline.tv_nsec -= 1_000_000_000
                deadline.tv_sec += 1
    finally:
        GPIO.cleanup()

if __name__ == '__main__':
    main()
