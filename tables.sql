CREATE TABLE players (
  player_id INTEGER PRIMARY KEY,
  player_name TEXT NOT NULL,
  hall_team TEXT NOT NULL,
  position TEXT NOT NULL,
  debut INTEGER NOT NULL,
  retired INTEGER NOT NULL
);

CREATE TABLE career_stats_hitting (
  id INTEGER PRIMARY KEY,
  player_id INTEGER,
  FOREIGN KEY (player_id) REFERENCES players(player_id),
  batting_average FLOAT,
  hits INTEGER,
  home_runs INTEGER,
  walks INTEGER,
  strikeouts INTEGER,
  stolen_bases INTEGER,
  h_war FLOAT
);

CREATE TABLE career_stats_pitching (
  id INTEGER PRIMARY KEY,
  player_id INTEGER,
  FOREIGN KEY (player_id) REFERENCES players(player_id),
  earned_run_average REAL NOT NULL,
  innings INTEGER NOT NULL,
  walks INTEGER NOT NULL,
  wins INTEGER NOT NULL,
  saves INTEGER NOT NULL,
  strikeouts INTEGER NOT NULL,
  p_war REAL NOT NULL
);

