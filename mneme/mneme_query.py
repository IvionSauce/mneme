#!/usr/bin/env python

import sys
from datetime import timedelta
from os import path

from mnemedt import mnemedt
from mneme_common import CONFIG, initialize_sqlite
from mneme_funcs import fmt_local, print_filehashes, replace_ws


##### HELPER FUNCTIONS #####

def get_arg(idx):
    if idx < len(sys.argv):
        return sys.argv[idx]
    else:
        return None

def fmt_grip_spec(dt, grip, grip_count):
    if grip_count > 1:
        return dt.strftime("%Y.%m.%d.{}".format(grip))
    else:
        return grip

def print_entry(row):
    file_loc, filename = tuple( map(replace_ws, path.split(row[0])) )
    # First use UTC timestamp to construct grip-spec.
    start = mnemedt.fromstr(row[1])
    grip_spec = fmt_grip_spec(start, row[4], row[5])
    # But convert to local datetime for displaying.
    start = fmt_local(start)
    if row[2]:
        stop = fmt_local(mnemedt.fromstr(row[2]))
        play_time = timedelta(seconds=row[3])
        print(
            "{}: [{}]\n@ {}\n[{}] {} ---> {}\n"
            .format(filename, play_time, file_loc, grip_spec, start, stop)
        )
    else:
        print(
            "{}: [NOW PLAYING]\n@ {}\n[{}] {} ---> ?\n"
            .format(filename, file_loc, grip_spec, start)
        )

def print_results(results, footer = False):
    count = 0
    for row in results:
        count += 1
        print_entry(row)
    print("-" * 72, file=sys.stderr)
    if footer:
        if count == 1:
            s = ""
        else:
            s = "s"
        print("Found {} event{} in media history."
              .format(count, s), file=sys.stderr)

def print_np(result):
    filename = path.basename(result[0])
    start_utc = mnemedt.fromstr(result[1])
    now_utc = mnemedt.now()
    # Calcute interim playing time and chop off microseconds.
    play_time = str(now_utc - start_utc)[:7]
    print(
        "{}: [{}]".format(replace_ws(filename), play_time)
    )

def print_files(results):
    for row in results:
        last_seen = mnemedt.fromstr(row[1])
        print(
            "{}\nLast seen: {}\n"
              .format(row[0], fmt_local(last_seen))
        )
    print("-" * 72, file=sys.stderr)


##### ENTRYPOINTS #####

# mneme <fs> [query]
def run_filesearch():
    if len(sys.argv) > 1:
        query = "%" + " ".join(sys.argv[1:]) + "%"
    else:
        query = "%"

    conn = initialize_sqlite()
    results = conn.execute(
        """SELECT filepath, last_seen_dt FROM filetrack
        WHERE filepath LIKE ?""",
        (query,)
    )
    print_files(results)

# mneme <latest|l> [count]
def run_latest():
    try:
        limit = int(get_arg(1))
    except (ValueError, TypeError):
        limit = CONFIG.latest_default_limit

    conn = initialize_sqlite()
    results = conn.execute(
        """SELECT
        filepath, start_dt, stop_dt, play_secs, h.grip, grip_count
        FROM history AS h
        JOIN filetrack ON filetrack.id = h.ftrack_id
        JOIN v_grips ON v_grips.grip = h.grip
        ORDER BY start_dt DESC LIMIT ?""",
        (limit,)
    ).fetchall()
    print_results(reversed(results))

# mneme <list-hashes|lh>
def run_list_hashes():
    conn = initialize_sqlite()
    results = conn.execute(
        "SELECT hash, filenames FROM files"
    )
    print_filehashes(results)

# mneme <playing|np>
def run_playing():
    conn = initialize_sqlite()
    result = conn.execute(
        """SELECT filepath, start_dt FROM history
        JOIN filetrack on filetrack.id = history.ftrack_id
        WHERE stop_dt IS NULL
        ORDER BY start_dt DESC LIMIT 1"""
    ).fetchone()
    if result:
        print_np(result)

# mneme <search|s> [query]
def run_search():
    if len(sys.argv) > 1:
        query = "%" + " ".join(sys.argv[1:]) + "%"
    else:
        query = "%"

    conn = initialize_sqlite()
    results = conn.execute(
        """SELECT
        filepath, start_dt, stop_dt, play_secs, h.grip, grip_count
        FROM history AS h
        JOIN filetrack ON filetrack.id = h.ftrack_id
        JOIN v_grips ON v_grips.grip = h.grip
        WHERE filepath LIKE ?
        ORDER BY start_dt""",
        (query,)
    )
    print_results(results, True)

# mneme <stats>
def run_stats():
    counts = []
    selects = (
        "SELECT count(id) FROM history",
        "SELECT count(id) FROM files",
        "SELECT count(id) FROM filetrack"
    )

    conn = initialize_sqlite()
    cur = conn.cursor()
    for s in selects:
        result = cur.execute(s).fetchone()
        counts.append(result[0])
    print(
        "I have knowledge of {} files and {} filepaths.\n"
        .format(counts[1], counts[2]) +
        "There are {} media events recorded in history."
        .format(counts[0])
    )
