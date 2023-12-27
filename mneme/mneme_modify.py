#!/usr/bin/env python

import re, sys
from mnemedt import mnemedt
from mneme_common import initialize_sqlite
from mneme_funcs import fmt_local, print_filehashes, replace_ws


def parse_purge_args():
    args = []
    for arg in sys.argv[1:]:
        m = re.fullmatch('[0-9a-f]{21,32}', arg)
        if m:
            args.append(m.string.zfill(32))
    return args

def parse_del_args():
    args = []
    for arg in sys.argv[1:]:
        m = re.fullmatch(
            '(?P<Y>[0-9]{4})?\.?' +
            '(?P<M>[0-9]{2})?\.?' +
            '(?P<D>[0-9]{2})?\.?' +
            '(?P<grip>[0-9a-f]{8})',
            arg
        )
        if m:
            date_q = ""
            for c in ('Y', 'M', 'D'):
                if m[c]:
                    date_q = date_q + m[c] + '-'
                else:
                    break
            date_q = date_q.removesuffix('-') + '%'
            args.append( (m["grip"], date_q) )
    return args

def cleanup(cur):
    ftrack_count = cur.execute(
        """SELECT count(id) FROM filetrack WHERE id NOT IN
        (SELECT ftrack_id FROM history)"""
    ).fetchone()
    file_count = cur.execute(
        """SELECT count(id) FROM files WHERE id NOT IN
        (SELECT file_id FROM history)"""
    ).fetchone()

    cur.executescript(
        """DELETE FROM filetrack WHERE id NOT IN
        (SELECT ftrack_id FROM history);

        DELETE FROM files WHERE id NOT IN
        (SELECT file_id FROM history);"""
    )
    return (ftrack_count[0], file_count[0])

def del_history(cur, grip_spec):
    result = cur.execute(
        """SELECT COUNT(grip), start_dt, filepath FROM history
        JOIN filetrack ON filetrack.id = history.ftrack_id
        WHERE grip=? AND start_dt LIKE ?""",
        grip_spec
    ).fetchone()

    if result[0] > 1:
        print("Grip {} has multiple matches, ".format(grip_spec[0]) +
              "please use a more specific grip-spec.", file=sys.stderr)
    elif result[0] == 1:
        ts = fmt_local(mnemedt.fromstr(result[1]))
        fp = replace_ws(result[2])
        print("{}\t{}\t{}".format(grip_spec[0], ts, fp))
        cur.execute(
            """DELETE FROM history
            WHERE grip=? AND start_dt LIKE ?""",
            grip_spec
        )

def del_yield_filehashes(cur, hashes_to_remove):
    for hash in hashes_to_remove:
        result = cur.execute(
            """DELETE FROM files WHERE hash=?
            RETURNING hash, filenames""",
            (hash,)
        ).fetchone()
        if result:
            yield result


##### ENTRYPOINTS #####

# mneme <cleanup>
def run_cleanup():
    conn = initialize_sqlite()
    cur = conn.cursor()
    # We manually start our (write) transaction here, because we start off with
    # SELECT queries, and we want to make sure the DB hasn't changed between
    # the SELECT queries and successive DELETE statements.
    cur.execute("BEGIN IMMEDIATE")
    counts = cleanup(cur)
    conn.commit()
    print("Removed {} filepaths and {} files, ".format(counts[0], counts[1]) +
          "since no history records reference them.", file=sys.stderr)

# mneme <del> <grip-spec...>
def run_delete():
    conn = initialize_sqlite()
    cur = conn.cursor()
    # We manually start our (write) transaction here, because we start off with
    # a SELECT query, and we want to make absolutely sure the DB hasn't changed
    # between the SELECT and subsequent DELETE statement.
    cur.execute("BEGIN IMMEDIATE")
    print("Deleting media events from history:\n", file=sys.stderr)
    for gpair in parse_del_args():
        del_history(cur, gpair)
    conn.commit()

# mneme <purge> <hash...>
def run_purge():
    conn = initialize_sqlite()
    cur = conn.cursor()
    print("Purging from all history records:\n", file=sys.stderr)
    print_filehashes(
        del_yield_filehashes(cur, parse_purge_args())
    )
    conn.commit()
