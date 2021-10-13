#!/usr/bin/python3
"""Advanced timekeeping features for Linux"""
# SPDX-FileCopyrightText: 2021 Jeff Epler
#
# SPDX-License-Identifier: GPL-3.0-only

# pylint: disable=invalid-name,missing-class-docstring,too-few-public-methods,missing-function-docstring,unused-import

import ctypes
import os
from time import CLOCK_TAI, CLOCK_REALTIME

TIMER_ABSTIME = 1

ADJ_OFFSET = 0x0001
ADJ_FREQUENCY = 0x0002
ADJ_MAXERROR = 0x0004
ADJ_ESTERROR = 0x0008
ADJ_STATUS = 0x0010
ADJ_TIMECONST = 0x0020
ADJ_TAI = 0x0080
ADJ_SETOFFSET = 0x100
ADJ_MICRO = 0x1000
ADJ_NANO = 0x2000
ADJ_TICK = 0x4000
ADJ_OFFSET_SINGLESHOT = 0x8001
ADJ_OFFSET_SS_READ = 0xA001

STA_PLL = 0x0001
STA_PPSFREQ = 0x0002
STA_PPSTIME = 0x0004
STA_FLL = 0x0008

STA_INS = 0x0010
STA_DEL = 0x0020
STA_UNSYNC = 0x0040
STA_FREQHOLD = 0x0080

STA_PPSSIGNAL = 0x0100
STA_PPSJITTER = 0x0200
STA_PPSWANTER = 0x0400
STA_PPSERROR = 0x0800

STA_CLOCKERR = 0x1000
STA_NANO = 0x2000
STA_MODE = 0x4000
STA_CLK = 0x8000

TIME_OK = 0
TIME_INS = 1
TIME_DEL = 2
TIME_OOP = 3
TIME_WAIT = 4
TIME_ERROR = 5


class timeval(ctypes.Structure):
    _fields_ = [
        ("tv_sec", ctypes.c_long),
        ("tv_usec", ctypes.c_long),
    ]


class timespec(ctypes.Structure):
    tv_sec: int
    tv_nsec: int
    _fields_ = [
        ("tv_sec", ctypes.c_long),
        ("tv_nsec", ctypes.c_long),
    ]


class timeunion(ctypes.Union):
    _fields_ = [
        ("time", timeval),
        ("time_ns", timespec),
    ]


class timex(ctypes.Structure):
    _anonymous_ = ("_",)
    _fields_ = [
        ("modes", ctypes.c_int),
        ("offset", ctypes.c_long),
        ("freq", ctypes.c_long),
        ("maxerror", ctypes.c_long),
        ("esterror", ctypes.c_long),
        ("status", ctypes.c_int),
        ("constant", ctypes.c_long),
        ("precision", ctypes.c_long),
        ("tolerance", ctypes.c_long),
        ("_", timeunion),
        ("tick", ctypes.c_long),
        ("ppsfreq", ctypes.c_long),
        ("jitter", ctypes.c_long),
        ("shift", ctypes.c_int),
        ("stabil", ctypes.c_long),
        ("jitcnt", ctypes.c_long),
        ("calcnt", ctypes.c_long),
        ("errcnt", ctypes.c_long),
        ("stbcnt", ctypes.c_long),
        ("tai", ctypes.c_int),
        ("", ctypes.c_int),
        ("", ctypes.c_int),
        ("", ctypes.c_int),
        ("", ctypes.c_int),
        ("", ctypes.c_int),
        ("", ctypes.c_int),
        ("", ctypes.c_int),
        ("", ctypes.c_int),
        ("", ctypes.c_int),
        ("", ctypes.c_int),
        ("", ctypes.c_int),
    ]


libc = ctypes.CDLL("libc.so.6", use_errno=True)
_clock_nanosleep = libc.clock_nanosleep
_clock_nanosleep.argtypes = [
    ctypes.c_int,
    ctypes.c_int,
    ctypes.POINTER(timespec),
    ctypes.POINTER(timespec),
]
_clock_nanosleep.restype = int

_ntp_adjtime = libc["ntp_adjtime"]
_ntp_adjtime.argtypes = [ctypes.POINTER(timex)]
_ntp_adjtime.restype = int


def ntp_adjtime(buf=None):
    buf = buf or timex()
    r = _ntp_adjtime(buf)
    if r < 0:
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno))
    return (r, buf)


NS_IN_S = 1_000_000_000

_clock_nanosleep = libc.clock_nanosleep
_clock_nanosleep.argtypes = [
    ctypes.c_int,
    ctypes.c_int,
    ctypes.POINTER(timespec),
    ctypes.POINTER(timespec),
]
_clock_nanosleep.restype = int


def clock_nanosleep_ts(clock, flags, request, res=None):
    res = res or timespec()
    r = _clock_nanosleep(clock, flags, request, res)
    if r < 0:
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno))
    return res.tv_sec * NS_IN_S + res.tv_nsec


def clock_nanosleep_ns(clock, flags, request, res=None):
    request = round(request)
    ts = timespec(request // NS_IN_S, request % NS_IN_S)
    return clock_nanosleep(  # pylint: disable=too-many-function-args
        clock, flags, ts, res
    )


def clock_nanosleep(clock, flags, request):
    return clock_nanosleep_ns(clock, flags, request * NS_IN_S) / NS_IN_S


_clock_gettime = libc.clock_gettime
_clock_gettime.argtypes = [ctypes.c_int, ctypes.POINTER(timespec)]
_clock_gettime.restype = int


def clock_gettime_ts(clock, buf=None):
    buf = buf or timespec()
    r = _clock_gettime(clock, buf)
    if r < 0:
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno))
    return buf


def clock_gettime_ns(clock):
    ts = clock_gettime_ts(clock)
    return ts.tv_sec * NS_IN_S + ts.tv_nsec


_clock_settime = libc.clock_settime
_clock_settime.argtypes = [ctypes.c_int, ctypes.POINTER(timespec)]
_clock_settime.restype = int


def clock_settime_ts(clock, buf):
    r = _clock_settime(clock, buf)
    if r < 0:
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno))
