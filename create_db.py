import csv
import sqlite3

db_con = sqlite3.connect('food_data.db')

# Database table definition

with db_con:
    db_con.execute(""" CREATE TABLE FoodData(
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        FoodCode TEXT,
        FoodName TEXT,
        Description TEXT,
        FoodGroup TEXT,
        Previous TEXT,
        Main_data_references TEXT,
        Footnote TEXT,
        WATER FLOAT,
        TOTNIT FLOAT,
        PROT FLOAT,
        FAT FLOAT,
        CHO FLOAT,
        KCALS FLOAT,
        KJ FLOAT,
        STAR FLOAT,
        OLIGO FLOAT,
        TOTSUG FLOAT,
        GLUC FLOAT,
        GALACT FLOAT,
        FRUCT FLOAT,
        SUCR FLOAT,
        MALT FLOAT,
        LACT FLOAT,
        ALCO FLOAT,
        ENGFIB FLOAT,
        AOACFIB FLOAT,
        SATFAC FLOAT,
        SATFOD FLOAT,
        TOTn6PFAC FLOAT,
        TOTn6PFOD FLOAT,
        TOTn3PFAC FLOAT,
        TOTn3PFOD FLOAT,
        MONOFACc FLOAT,
        MONOFODc FLOAT,
        MONOFAC FLOAT,
        MONOFOD FLOAT,
        POLYFACc FLOAT,
        POLYFODc FLOAT,
        POLYFAC FLOAT,
        POLYFOD FLOAT,
        SATFACx6 FLOAT,
        SATFODx6 FLOAT,
        TOTBRFAC FLOAT,
        TOTBRFOD FLOAT,
        FACTRANS FLOAT,
        FODTRANS FLOAT,
        CHOL FLOAT,
        Favourite BINARY
        );
    """)


# SQL command to create import the data.
sql = 'INSERT INTO FoodData (\
FoodCode, FoodName,Description, FoodGroup, Previous, Main_data_references, Footnote, WATER, TOTNIT, PROT, FAT, CHO,\
KCALS,          KJ,       STAR, OLIGO,   TOTSUG,                 GLUC,   GALACT, FRUCT,   SUCR, MALT,LACT,ALCO,\
ENGFIB,    AOACFIB,     SATFAC,SATFOD,TOTn6PFAC, TOTn6PFOD,TOTn3PFAC,TOTn3PFOD, MONOFACc, MONOFODc,MONOFAC, MONOFOD,\
POLYFACc, POLYFODc, POLYFAC, POLYFOD, SATFACx6, SATFODx6, TOTBRFAC, TOTBRFOD, FACTRANS, FODTRANS, CHOL, Favourite)\
values(\
?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,\
?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,\
?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,\
?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)'

data = []

# Open and process the CSV file that has the mapping between the strands/pixels and stations/Lines.
with open('McCance_Widdowsons_Composition_of_Foods_Integrated_Dataset_2021Simplified.csv', newline='',
          encoding= 'utf-16') as food_data_file:
    food_reader = csv.reader(food_data_file, delimiter=',', quotechar='"')
    for row in food_reader:
        # station_data = [row[0], row[1], row[2], row[3]]
        data.append(row)

    # print(data)

# Populate data table with the imported CSV file.
with db_con:
    print(sql)

    for data_row in data[3:]:
        print(data_row)
        db_con.execute(sql, data_row)

    food_data = db_con.execute("SELECT * FROM FoodData")

    for food in food_data:
        print(food)