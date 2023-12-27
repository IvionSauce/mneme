#!/usr/bin/env python

import sqlite3, tomllib
from pathlib import Path

VERSION = "0.8.0"


class config:
    def __init__(self):
        default_config = """# Configuration file for the media history application, mneme.
db_file = "~/.local/share/mneme_db.sqlite"
media_player = "mpv"
datetime_display_format = "%Y-%m-%d %H:%M:%S %Z"
latest_default_limit = 10
"""
        a = Path.home() / ".config" / "mneme.toml"
        b = Path.home() / ".mneme.toml"
        if a.is_file():
            config_file = a
        elif b.is_file():
            config_file = b
        else:
            with(open(a, "w") as f):
                f.write(default_config)
            config_file = a

        with (open(config_file, "rb") as f):
            self.conf = tomllib.load(f)
        # Expand ~ in db_file path:
        self.conf["db_file"] = Path(self.conf["db_file"]).expanduser()

    def __getattr__(self, name):
        val = self.conf.get(name)
        if val:
            return val
        else:
            raise AttributeError(
                "'config' object has no attribute '{}'".format(name)
            )
CONFIG = config()

def initialize_sqlite():
    db_conn = sqlite3.connect(CONFIG.db_file)
    db_conn.executescript(
"""PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS
files(
  id INTEGER PRIMARY KEY ASC,
  hash TEXT NOT NULL UNIQUE,
  filenames TEXT NOT NULL,
  renames INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS
filetrack(
  id INTEGER PRIMARY KEY ASC,
  file_id INTEGER NOT NULL,
  filepath TEXT NOT NULL,
  first_seen_dt TEXT NOT NULL,
  last_seen_dt TEXT NOT NULL,
  FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS
history(
  id INTEGER PRIMARY KEY ASC,
  file_id INTEGER NOT NULL,
  ftrack_id INTEGER NOT NULL,
  start_dt TEXT NOT NULL,
  stop_dt TEXT,
  play_secs INTEGER,
  grip TEXT NOT NULL,
  FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE,
  FOREIGN KEY(ftrack_id) REFERENCES filetrack(id) ON DELETE CASCADE
);

CREATE VIEW IF NOT EXISTS
v_grips(grip, grip_count)
AS SELECT grip, count(grip) FROM history
GROUP BY grip;

CREATE INDEX IF NOT EXISTS
history_idx1 ON history(ftrack_id);

CREATE INDEX IF NOT EXISTS
history_idx2 ON history(start_dt);

CREATE INDEX IF NOT EXISTS
history_idx3 ON history(grip);

CREATE UNIQUE INDEX IF NOT EXISTS
filetrack_uniq ON filetrack(file_id, filepath);"""
    )
    db_conn.commit()
    return db_conn
