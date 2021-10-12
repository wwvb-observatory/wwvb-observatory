# WWVB Observatory

An archive of WWVB data as received by a low-end receiver at my house

# The receiver

The receiver consists of a Raspberry Pi 4 connected to a [CANADUINO 60kHz Atomic Clock Receiver](https://www.universal-solder.ca/product/canaduino-60khz-atomic-clock-receiver-module-wwvb-msf-jjy60/) with MAS6180C receiver IC.

The Pi is reasonably well synchronized to GPS time via NTP.

Per the datasheet, the MAS618C receiver introduces a phase shift of 50ms
(typical) to 100ms (max) in the demodulated signal.

# The log file

Logfiles are split according to the UTC day, so they consist of filenames like `2021/09-01.txt`.

The log file consists mostly of lines that start by giving the Pi system time
in UTC `YYYY-mm-dd HH:MM:SS` format, followed by 50 samples of the
amplitude-modulated signal taken during the second (nominally 20ms apart). Each
sample is represented by a `_` or a `#`. `#` represents the full-strength
carrier period and `_` represents the reduced carrier period.

The line also contains "|" symbols which divide the second into
 * The time when the carrier should always be full-strength
 * The time when the carrier has been reduced for a "0" symbol transmission
 * The time when the carrier has been reduced for a "1" symbol transmission
 * The time when the carrier should always be reduced

# The upload process

From time to time, the latest logfiles from the in-house device are committed to this git repository.  Intially, the process will be purely manual.

# Future directions

 - Show historical data on github.io
 - Log analysis for anomalies
 - Live view via website
 - Additional receivers
 - Switch to TAI timebase so that leap seconds can be observed(?)

# License

The Python scripts are licensed GPL-3.  The logs, if subject to copyright, are
licensed CC0.
