from concurrent.futures.process import ProcessPoolExecutor
import datetime
from dataclasses import dataclass
from functools import cached_property, lru_cache
from typing import List
from itertools import count

import click
from tqdm import tqdm
from leapseconddata import LeapSecondData, tai
from wwvb import WWVBMinuteIERS

ls = LeapSecondData.from_standard_source()


@lru_cache(1440)
def am_from_datetime(observation_time):
    return WWVBMinuteIERS.from_datetime(observation_time).as_timecode().am


def reference_minute(observation_time):
    if observation_time.tzinfo is None:
        raise ValueError("Naive datetime object not accepted")
    if observation_time.tzinfo is tai:
        observation_time = ls.tai_to_utc(observation_time)
    if observation_time.tzinfo is not datetime.timezone.utc:
        observation_time = observation_time.astimezone(datetime.timezone.utc)

    second = observation_time.second + observation_time.fold
    observation_time = observation_time.replace(second=0, microsecond=0)

    return (am_from_datetime(observation_time), second)


@dataclass(frozen=True)
class WWVBObservationSecond:
    tai_time: datetime.datetime
    samples: str

    def __repr__(self):
        mismatch = "" if self.matches_reference else "!={+self.reference}"
        return (
            f"<{self.tai_time:%Y-%m-%d %H:%M:%S} TAI "
            f"{self.symbol}{mismatch} "
            f"Q{self.quality}>"
        )

    @classmethod
    def from_string(cls, data):
        data = data.rstrip("\n")
        if len(data) != 77:
            return None
        parts = data.split(" TAI ", 1)
        if len(parts) != 2:
            return Nonea
        samples = parts[1].replace("|", "")
        tai_time = datetime.datetime.fromisoformat(parts[0]).replace(tzinfo=tai)
        return cls(tai_time, samples)

    @property
    def utc_time(self):
        return ts.tai_to_utc(self.tai_time)

    @property
    def is_leap_second(self):
        return ts.is_leap_second(self.tai_time)

    @cached_property
    def divisions(self):
        s = self.samples
        return [s[:10], s[10:25], s[25:40], s[40:]]

    @property
    def counts(self):
        return [s.count("_") for s in self.divisions]

    @property
    def symbol(self):
        a, b, c, d = self.counts
        if c > 9:
            return 2
        if b > 9:
            return 1
        return 0

    @property
    def quality(self):
        if not self.matches_reference:
            return 0

        symbol = self.symbol
        if symbol == 0:
            nom = (10, 0, 0, 0)
        elif symbol == 1:
            nom = (10, 15, 0, 0)
        else:
            nom = (10, 15, 15, 0)
        return 100 - 2 * sum(abs(ci - ni) for ci, ni in zip(self.counts, nom))

    @property
    def reference(self):
        wwvbminute, second = reference_minute(self.tai_time)
        return wwvbminute[second]

    @cached_property
    def matches_reference(self):
        return self.reference == self.symbol


@dataclass
class WWVBObservationLog:
    observations: List[WWVBObservationSecond]

    @classmethod
    def from_file(cls, f):
        return WWVBObservationLog(
            [
                observation
                for row in f
                if (observation := WWVBObservationSecond.from_string(row))
            ]
        )

    @classmethod
    def from_filename(cls, filename):
        with open(filename, "rt", encoding="utf-8") as f:
            return cls.from_file(f)

    @classmethod
    def from_url(cls, url):
        import requests  # pylint: disable=invalid-import-location

        with requests.get(url) as response:
            return WWVBObservationLog(
                [
                    WWVBObservationSecond.from_string(line)
                    for line in response.iter_lines(decode_unicode=True)
                ]
            )

    def __iter__(self):
        return iter(self.observations)

    @property
    def mismatches(self):
        return sum(not m.matches_reference for m in self)

    @property
    def quality(self):
        return sum(m.quality for m in self) / len(self.observations)

def process(filename):
    stats = WWVBObservationLog.from_filename(filename)
    if not stats.observations:
        return filename, None
    else:
        return filename, (stats.observations[0].tai_time, len(stats.observations), stats.mismatches, stats.quality)

@click.command()
@click.option("--verbose", "-v", type=bool, default=False)
@click.argument("files", type=click.Path(exists=True), nargs=-1)
def main(verbose, files):
    pool = ProcessPoolExecutor()
    for filename, data in tqdm(pool.map(process, files), total=len(files)):
        if not data:
            print(f"{infile} contains no observations", file=stderr)
        else:
            tai_time, n_obs, n_mis, q = data
            if verbose:
                print(
                    f"{infile}:0: {n_mis} in {n_obs} observations ({n_mis*100/n_obs:.1f}%) overall quality {q:.1f}"
                )
            else:
                print(
                    f"{tai_time:%Y-%m-%d %H:%M:%S} TAI {n_obs} {n_mis*100/n_obs:.1f} {q:.1f}"
                )


if __name__ == "__main__":
    main()
