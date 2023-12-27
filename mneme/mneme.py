#!/usr/bin/env python

import sys
from os import path
from mneme_common import CONFIG, VERSION


def show_help(script_name):
    print(
"""Usage: {0} <command> [args...]

Commands:

  cleanup        Scan events and cleanup files and filepaths unreferenced by
                 records in history.
  delete, del    Delete media events from history by passing their grip or
                 grip-spec as arguments.
  fsearch, fs    Searches for media files and their last known location, the
                 arguments being the search query.
  hash, h        Computes sampling hash for files passed as arguments.
  latest, l      Lists latest media events entries in history; defaults to
                 last {1}, but one can pass any limit as argument.
  hashes, lh     Lists all recorded hashes and filenames.
  playing, np    Prints currently active media event, if any.
  purge          Purges history records of files that match the hashes passed
                 as arguments.
  search, s      Searches through history for the media events, the arguments
                 being the search query.
  stats          Gives some simple stats about files, filepaths and the history.
  version        Prints version information.
  wrapper, w     Records the event into history and passes the arguments along
                 to the configured media player.

GRIP-SPEC:
Functions as an identifier for a media event, it's format is:
[YYYY.[MM.[DD.]]]<GRIP>. The year, month and day parts are each
optional, unless there are multiple events with the same grip."""
        .format(script_name, CONFIG.latest_default_limit),
        file=sys.stderr
    )

def run_mneme():
    script = path.basename(sys.argv[0])
    if len(sys.argv) > 1:
        command = sys.argv[1]
        sys.argv = sys.argv[1:]
        match command:

            case "add":
                from mneme_misc import run_add
                run_add()

            case "cleanup":
                from mneme_modify import run_cleanup
                run_cleanup()

            case "delete" | "del":
                from mneme_modify import run_delete
                run_delete()

            case "fsearch" | "fs":
                from mneme_query import run_filesearch
                run_filesearch()

            case "hash" | "h":
                from mneme_digests import sampling_hash
                from mneme_funcs import replace_ws
                files = sys.argv[1:]
                for f in files:
                    if path.isfile(f):
                        print("{}  {}".format(sampling_hash(f), replace_ws(f)))

            case "latest" | "l":
                from mneme_query import run_latest
                run_latest()

            case "hashes" | "lh":
                from mneme_query import run_list_hashes
                run_list_hashes()

            case "playing" | "np":
                from mneme_query import run_playing
                run_playing()

            case "purge":
                from mneme_modify import run_purge
                run_purge()

            case "search" | "s":
                from mneme_query import run_search
                run_search()

            case "stats":
                from mneme_query import run_stats
                run_stats()

            case "version" | "--version":
                print("mneme {}".format(VERSION), file=sys.stderr)

            case "wrapper" | "w":
                from mneme_wrapper import run_wrapper
                run_wrapper()

            case _:
                show_help(script)
    else:
        show_help(script)

if __name__ == "__main__":
    run_mneme()
