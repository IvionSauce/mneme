#!/usr/bin/env python

import sys
from mnemedt import mnemedt
from mneme_common import initialize_sqlite
from mneme_digests import history_grip
from mneme_wrapper import get_file_id, update_filetrack, yield_files


def run_add():
    conn = initialize_sqlite()
    cur = conn.cursor()

    timestamp = mnemedt.now()
    count = 0
    for filepath in yield_files():
        file_id = get_file_id(cur, filepath)
        update_filetrack(cur, file_id, filepath, timestamp)
        count += 1
    conn.commit()

    print("Processed {} file(s).".format(count), file=sys.stderr)

def run_calc_grips():
    conn = initialize_sqlite()

    results = conn.execute(
        """SELECT id, file_id, ftrack_id, start_dt, stop_dt FROM history
        WHERE stop_dt IS NOT NULL"""
    )
    for row in results:
        grip = history_grip(row[:3], row[3:])
        conn.execute(
            "UPDATE history SET grip=? WHERE id=?", (grip, row[0])
        )
    conn.commit()
