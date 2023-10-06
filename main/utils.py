from typing import Protocol


class DateFormatable(Protocol):
    def strftime(self, __format: str) -> str:
        ...


REPR_FORMAT = r"%d.%m.%Y %H:%M"
OFFICIAL_FORMAT = r"%Y-%m-%d %H:%M:%S"


def repr_format(d: DateFormatable):
    return d.strftime(REPR_FORMAT)


def official_format(d: DateFormatable):
    return d.strftime(OFFICIAL_FORMAT)
