import collections
import sys
import time
import RPi.GPIO as GPIO
import wwvb
from clock_nanosleep import (
    CLOCK_REALTIME,
    TIMER_ABSTIME,
    clock_gettime_ts,
    clock_nanosleep_ts,
    timespec,
)

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
            self._filename = filename
            if self._file is not None:
                self._file.close()
            self._file = open(filename, 'a')

    def write(self, buf):
        return self._file.write(buf)

    def flush(self):
        return self._file.flush()

now = clock_gettime_ts(CLOCK_REALTIME)
deadline = timespec(now.tv_sec + 1, 0)
logfile = DatedFile(deadline.tv_sec, "wwvb-%Y-%m-%d.txt")
sys.stdout = Tee(sys.stdout, logfile)

GPIO.setmode(GPIO.BOARD)
PINS = [3,5]
PIN = 3
GPIO.setup(PINS, GPIO.IN)
# loop through 50 times, on/off for 1 second
last_second = 0


r = []
s = collections.deque([wwvb.AmplitudeModulation.MARK]*60, 60)
try:
    while True:
        clock_nanosleep_ts(CLOCK_REALTIME, TIMER_ABSTIME, deadline)
        st = GPIO.input(PIN)
        i = deadline.tv_nsec // 10_000_000
        if deadline.tv_nsec == 0:
            if r:
                pt0 = sum(r[0:10]) / 10
                pt1 = sum(r[10:25]) / 15
                pt2 = sum(r[25:40]) / 15
                pt3 = sum(r[40:50]) / 10
                if pt1 > .5:
                    if pt2 > .5:
                        result = "M"
                        s.append(wwvb.AmplitudeModulation.MARK)
                    else:
                        result = "1"
                        s.append(wwvb.AmplitudeModulation.ONE)
                else:
                    result = "0"
                    s.append(wwvb.AmplitudeModulation.ZERO)
                print(f" {result}")
            tc = wwvb.WWVBTimecode(60)
            tc.am[:] = s
            minute = wwvb.WWVBMinute.from_timecode_am(tc)
            if minute:
                print(f"# {minute}")
            logfile.timestamp = deadline.tv_sec
            g = time.gmtime(deadline.tv_sec)
            print(end=f'{time.strftime("%Y-%m-%d %H:%M:%SZ ", g)}')
            r = []

        r.append(st)
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
