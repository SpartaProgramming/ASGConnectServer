import sqlite3
import logging
from datetime import datetime

DB_PATH = 'game_history.db'

def init_db():
    """Tworzy tabele, jeśli nie istnieją."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Tabela konfiguracji meczów
    cursor.execute('''CREATE TABLE IF NOT EXISTS match_configs
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       timestamp TEXT,
                       game_type TEXT,
                       red_team TEXT,
                       blue_team TEXT)''')

    # Tabela logów trafień (do statystyk)
    cursor.execute('''CREATE TABLE IF NOT EXISTS hits
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       timestamp TEXT,
                       victim_eui TEXT,
                       team TEXT)''')
    conn.commit()
    conn.close()

def save_config_to_db(game_type, teams_dict):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO match_configs (timestamp, game_type, red_team, blue_team) VALUES (?, ?, ?, ?)",
                       (datetime.now().isoformat(),
                        game_type,
                        ",".join(teams_dict.get('RED', [])),
                        ",".join(teams_dict.get('BLUE', []))))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Błąd zapisu do bazy: {e}")

def log_hit_to_db(victim_eui, team="UNKNOWN"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO hits (timestamp, victim_eui, team) VALUES (?, ?, ?)",
                   (datetime.now().isoformat(), victim_eui, team))
    conn.commit()
    conn.close()