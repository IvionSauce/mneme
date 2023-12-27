#!/usr/bin/env python

import json, subprocess, sys
from os import path

from mnemedt import mnemedt
from mneme_common import CONFIG, initialize_sqlite
from mneme_digests import history_grip, sampling_hash


##### DATABASE FUNCTIONS #####

def json_serialize(lst_or_str):
    if isinstance(lst_or_str, str):
        to_dump = [lst_or_str]
    elif isinstance(lst_or_str, list):
        to_dump = lst_or_str
    else:
        raise ValueError("Unexpected type for serialization")

    return json.dumps(to_dump, ensure_ascii=False)

def update_filenames(cur, f_id, filenames, new_filename):
    curr_names = json.loads(filenames)
    if not new_filename in curr_names:
        curr_names.append(new_filename)
        cur.execute(
            "UPDATE files SET filenames=?, renames=renames+1 where id=?",
            (json_serialize(curr_names), f_id)
        )

def get_file_id(cur, fpath):
    file_hash = sampling_hash(fpath)
    filename = path.basename(fpath)

    result = cur.execute(
        "SELECT id, filenames FROM files WHERE hash=?", (file_hash,)
    ).fetchone()

    if result:
        file_id = result[0]
        update_filenames(cur, file_id, result[1], filename)
    else:
        cur.execute(
            "INSERT INTO files(hash, filenames) VALUES(?, ?)",
            (file_hash, json_serialize(filename))
        )
        file_id = cur.lastrowid

    return file_id

def update_filetrack(cur, file_id, fpath, timestamp):
    fullpath = path.abspath(fpath)
    ts = str(timestamp)

    result = cur.execute(
        """INSERT INTO filetrack VALUES(NULL, ?, ?, ?, ?)
        ON CONFLICT(file_id, filepath) DO UPDATE SET last_seen_dt=?
        RETURNING id""",
        (file_id, fullpath, ts, ts, ts)
    ).fetchone()
    return result[0]

def record_start(cur, file_id, ftrack_id, timestamp_start):
    ts = str(timestamp_start)
    # Compute (temporary) grip for history event.
    grip = history_grip( (file_id, ftrack_id), (ts,) )

    # Record into history what we're watching and when we started.
    cur.execute(
        """INSERT INTO history(file_id, ftrack_id, start_dt, grip)
        VALUES(?, ?, ?, ?)""",
        (file_id, ftrack_id, ts, grip)
    )
    return cur.lastrowid

def record_stop(cur, hist_id, timestamp_stop, play_time):
    ts = str(timestamp_stop)
    # Fetch necessary values and compute final grip for history event.
    result = cur.execute(
        "SELECT id, file_id, ftrack_id, start_dt FROM history WHERE id=?",
        (hist_id,)
    ).fetchone()
    if result:
        grip = history_grip( result[:3], (result[3], ts) )
        # Update history record: when we stopped and how long we were watching.
        play_secs = int(play_time.total_seconds() + 0.5)
        cur.execute(
            "UPDATE history SET stop_dt=?, play_secs=?, grip=? WHERE id=?",
            (ts, play_secs, grip, hist_id)
        )


##### SCRIPT #####

def yield_files():
    mode = "check"
    for i in range(1, len(sys.argv)):
        arg = path.expanduser(sys.argv[i])

        if mode == "check":
            if arg == "--":
                mode = "pass"
            elif not arg.startswith("-") and path.isfile(arg):
                yield arg
        elif mode == "pass" and path.isfile(arg):
            yield arg

def run_wrapper():
    before = mnemedt.now()
    # Media player START!
    media_player = subprocess.Popen([CONFIG.media_player] + sys.argv[1:])

    conn = initialize_sqlite()
    cur = conn.cursor()

    # We manually start our (write) transaction here, because we start off with
    # a SELECT query, and we don't want any writes sneaking in between the
    # SELECT and subsequent INSERT/UPDATE statements.
    cur.execute("BEGIN IMMEDIATE")
    hist_ids = []
    for filepath in yield_files():
        file_id = get_file_id(cur, filepath)
        ftrack_id = update_filetrack(cur, file_id, filepath, before)

        hist_ids.append(record_start(cur, file_id, ftrack_id, before))
    conn.commit()

    # Media player STOP!
    media_player.wait()
    after = mnemedt.now()
    play_time = after - before

    for hist_id in hist_ids:
        record_stop(cur, hist_id, after, play_time)
    conn.commit()

if __name__ == "__main__":
    run_wrapper()
