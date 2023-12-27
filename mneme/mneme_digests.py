#!/usr/bin/env python

# Sample size for building file checksum.
CK_SAMPLE_SIZE = 16 * 1024
# Initial value and multiplier for building skip list.
SKIP_VALUES = (1 * 1024**2, 8)
# Balance between the digest/checksum and filesize contribution to
# the final checksum (in bytes each).
CK_BALANCE = (10, 6)
# Digest size for the history handle, in bytes.
HIST_HANDLE_SIZE = 4

import math
from hashlib import blake2b
from os import path


def insert_into(l, value):
    for i in range(len(l) - 1):
        j = i + 1
        if value > l[i] and value < l[j]:
            l.insert(j, value)
            return

def sample_locations(filesize):
    end_location = filesize - CK_SAMPLE_SIZE
    # Prepend sample location at file's beginning.
    skip_list = [0]
    # Skip around the file, selecting locations with an ever increasing skip.
    curr_skip = SKIP_VALUES[0]
    while curr_skip < end_location:
        skip_list.append(curr_skip)
        curr_skip = curr_skip * SKIP_VALUES[1]
    # Append sample location at file's end.
    skip_list.append(end_location)
    # Insert sample location at midpoint of the file.
    middle = math.floor(filesize / 2)
    insert_into(skip_list, middle)
    return skip_list

def checked_getsize(filepath):
    fsize = path.getsize(filepath)
    bitwidth = CK_BALANCE[1] * 8
    if fsize > 2**bitwidth - 1:
        raise OverflowError(
            "File size doesn't fit inside {} bytes/{} bits!"
            .format(CK_BALANCE[1], bitwidth)
        )
    else:
        return fsize

def _do_sampling(hasher, filepath, filesize):
    with open(filepath, 'rb') as f:
        for loc in sample_locations(filesize):
             f.seek(loc)
             hasher.update(f.read(CK_SAMPLE_SIZE))

def sampling_hash(filepath):
    fsize = checked_getsize(filepath)
    h = blake2b(digest_size=CK_BALANCE[0])
    if fsize > 0:
        _do_sampling(h, filepath, fsize)

    concat_hash = int.from_bytes(
        fsize.to_bytes(CK_BALANCE[1]) + h.digest()
    )
    padding = 2 * sum(CK_BALANCE)
    return "{0:0{1}x}".format(concat_hash, padding)

def history_grip(indices, datetimes):
    h = blake2b(digest_size=HIST_HANDLE_SIZE)
    for date in datetimes:
        h.update( bytes(str(date), "ascii") )
    for i in indices:
        byte_length = math.ceil(i.bit_length() / 8)
        h.update( i.to_bytes(byte_length) )
    return h.hexdigest()
