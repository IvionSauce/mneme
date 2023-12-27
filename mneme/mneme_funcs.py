#!/usr/bin/env python

import json
from mneme_common import CONFIG


def fmt_local(timestamp):
    return timestamp.localdt().strftime(CONFIG.datetime_display_format)

def print_filehashes(results):
    for row in results:
        filenames = json.loads(row[1])
        print("{}\t{}".format(row[0], filenames))

def replace_ws(s):
    val = [c for c in s]
    for i in range(len(val)):
        match ord(val[i]):
            # Horizontal Tab.
            case 0x9:
                val[i] = r'\t'
            # Line Feed.
            case 0xA:
                val[i] = r'\n'
            # Carriage Return.
            case 0xD:
                val[i] = r'\r'

            # Backslash (\).
            case 0x5C:
                val[i] = r'\\'

    return ''.join(val)
