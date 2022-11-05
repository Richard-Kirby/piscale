import sqlite3

history_db_con = sqlite3.connect('history.db')

with history_db_con:
    history_db_con.execute(""" CREATE TABLE History(
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        Date TEXT,
        KCALS FLOAT,
        WEIGHT INTEGER
        );
    """)

