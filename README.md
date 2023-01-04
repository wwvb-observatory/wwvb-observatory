<!--
SPDX-FileCopyrightText: 2021 Jeff Epler

SPDX-License-Identifier: GPL-3.0-only
-->

# WWVB Observatory

An archive of WWVB data as received by a low-end receiver at my house, including data for most of 2022.

As of January 2023, the observatory has been mothballed. If something interesting happens, like a leap second, I might operate it again for the occasion.

# The receiver

The receiver consisted of a Raspberry Pi 4 connected to a [CANADUINO 60kHz Atomic Clock Receiver](https://www.universal-solder.ca/product/canaduino-60khz-atomic-clock-receiver-module-wwvb-msf-jjy60/) with MAS6180C receiver IC.  It was located in Lincoln, Nebraska, USA, or around 700km east of the transmitter.

The Pi was reasonably well synchronized to GPS time via NTP.

Per the datasheet, the MAS618C receiver introduces a phase shift of 50ms
(typical) to 100ms (max) in the demodulated signal.

# The log file

Logfiles are split according to the TAI date and hour, so they consist of filenames like `2021/09-01/01.txt`.

A typical line reads:
```
2021-10-13 15:40:59 TAI ####______|_______________|_______________|__########
```
The first fields give the date, time, and timescale, currently TAI.

The time fields are followed by 50 samples of the
amplitude-modulated signal taken during the second (nominally 20ms apart). Each
sample is represented by a `_` or a `#`. `#` represents the full-strength
carrier period and `_` represents the reduced carrier period.

The period of full-strength carrier shown at the start of the second is an
artifact of the phase shift introduced by the MAS618C receiver.

The line also contains "|" symbols which divide the second into 4 portions according to the nominal WWVB bit framing:
 * The time when the carrier is always reduced
 * The time when the carrier is restored for a "0" symbol transmission
 * The time when the carrier is restored for a "1" symbol transmission
 * The time when the carrier is always full-strength

Since the TAI timescale technically continues to advance during a leap second,
the author hopes using it allows leap seconds to be correctly observed.
However, it is difficult to actually test this.


# The upload process

After each log is rotated away, it is committed to git.  Later, it will automatically be pushed to github.


# License

The Python scripts are licensed GPL-3.  The logs, if subject to copyright, are
licensed CC0.
