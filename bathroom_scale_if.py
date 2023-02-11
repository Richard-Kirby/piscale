import socket
import threading
import sqlite3 as sql
import pathlib
from datetime import datetime, timedelta

import logging

logger = logging.getLogger('scaleLogger')

mod_path = pathlib.Path(__file__).parent

# Class to manage the interface ot the Bathroom scale. Receives UDP messages, throwing out duplicates and adds them
# to a database which can then be queried.
class BathroomScaleIF(threading.Thread):
    def __init__(self, udp_ip_port):
        threading.Thread.__init__(self)

        self.sock = socket.socket(socket.AF_INET, # Internet
                             socket.SOCK_DGRAM) # UDP
        self.sock.bind(udp_ip_port)

        # Connect to the DB.
        self.body_weight_db = sql.connect(f'{mod_path}/body_weight_history.db', check_same_thread=False)

        # Create the Meal History DB tables if not already created.
        with self.body_weight_db:

            # create cursor object - this part is to create the initial table if it doesn't exist yet.
            cur = self.body_weight_db.cursor()

            list_of_tables = cur.execute(
                """SELECT name FROM sqlite_master WHERE type='table'
                AND name='BodyWeightHistory'; """).fetchall()

            # print(list_of_tables)

            if list_of_tables == []:
                print("Table not found, creating Body Weight History")

                # Create the table as it wasn't found.
                self.body_weight_db.execute(""" CREATE TABLE BodyWeightHistory(
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        Date TEXT,
                        User TEXT,
                        Weight FLOAT
                        );
                    """)

    # Thread's run function receives data and processes the received body weights by adding them to the DB.
    def run(self):
        last_msg_received_time = None
        print("run")

        # Receive UDP messages from the scale, throw away duplicates.
        while True:
            data, addr = self.sock.recvfrom(1024) # buffer size is 1024 bytes

            # Get time of the message, strip out surrounding junk and compare to other
            # messages to throw out duplicates.
            now = datetime.now()
            result = str(data).split(',')
            weight = float(result[1][:-1].strip())

            if last_msg_received_time is None:
                last_msg_received_time = now
                print(f"received message:{now}, {data}, {result}, {weight}")
                with self.body_weight_db:

                    # Add to body weight history
                    self.body_weight_db.execute("INSERT INTO BodyWeightHistory (Date, User, Weight) values(?, ?, ?)"
                                                , [now, "Richard", weight])

            # Ensure the message is actually a new measurement - Scale sends multiple messages to ensure the measurement
            # is received.
            else:
                time_diff = now-last_msg_received_time

                if time_diff > timedelta(minutes=1):
                    print("new measurement")
                    last_msg_received_time = now
                    print(f"received message:{now}, {data}, {result}, {weight}")

                    with self.body_weight_db:

                        # Add to body weight history
                        self.body_weight_db.execute("INSERT INTO BodyWeightHistory (Date, User, Weight) values(?, ?, ?)"
                             ,[now, "Richard", weight])

    # Provide database records to the caller. num_records of 0 will return all records.
    def return_records(self, num_records =0 ):
        body_weight_history = self.body_weight_db.execute("SELECT id, Date, User,Weight FROM BodyWeightHistory")

        ret_list = []

        for item in body_weight_history:
            #print(item)
            ret_list.append(item)

        if num_records ==0:
            return ret_list
        else:
            return ret_list[:-num_records]

    # Deletes the record entry in the database according to ID
    def delete_entry(self, db_id):
        self.body_weight_db.execute("DELETE FROM BodyWeightHistory WHERE id = ?", (db_id,))
        print(f"Deleted {db_id}")
        self.body_weight_db.commit()


if __name__ == '__main__':

    bath_if = BathroomScaleIF(("255.255.255.255", 6000))

    bath_if.start()

    body_weight_history = bath_if.return_records(num_records=2)
    print(body_weight_history)

