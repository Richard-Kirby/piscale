import sqlite3

cal_db_con = sqlite3.connect('meal_history.db')

# Database table definition

with cal_db_con:
    cal_db_con.execute(""" CREATE TABLE Calories_measured(
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        FoodName TEXT,
        PROT FLOAT,
        FAT FLOAT,
        CHO FLOAT,
        KCALS FLOAT,
        WEIGHT FLOAT
        );
    """)

history_db_con = sqlite3.connect('history.db')

with history_db_con:
    history_db_con.execute(""" CREATE TABLE History(
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        Date TEXT,
        KCALS FLOAT,
        WEIGHT INTEGER
        );
    """)

