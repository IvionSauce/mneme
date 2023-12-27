#!/usr/bin/env python

from datetime import datetime, timezone


class mnemedt:
    # DateTime format for serializing to the DB.
    _dtformat = "%Y-%m-%dT%H:%M:%S.%fZ"

    def __init__(self, dt_val):
        if dt_val.tzinfo != timezone.utc:
            raise ValueError("Timezone must be UTC")
        self.datetime = dt_val

    @staticmethod
    def now():
        return mnemedt(datetime.now(timezone.utc))

    @staticmethod
    def fromstr(dt_str):
        return mnemedt(datetime.fromisoformat(dt_str))

    def localdt(self):
        return self.datetime.astimezone()

    def __getattr__(self, name):
        try:
            return self.datetime.__getattribute__(name)
        except AttributeError as ex:
            raise AttributeError(
                "'mnemedt' object has no attribute '{}'".format(name)
            ) from ex

    def __sub__(self, other):
        return self.datetime - other.datetime

    def __str__(self):
        return self.datetime.strftime(self._dtformat)

    def __repr__(self):
        return self.datetime.__repr__()
