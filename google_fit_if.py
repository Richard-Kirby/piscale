#!/usr/bin/python3
# Google Fitness Interface Class to connect to Google via its REST interface. It processes the available credentials
# in the client_secrets.json. Using Oauth2Client, specific authorisation tokens are saved in the fitness.dat file.
#
# The fitness.dat authorisations will be sorted out if not available when run, but the clients_secrets.json file
# needs to be sorted out via the Google Developer process.URL below for this particular application.
#
# https://console.cloud.google.com/apis/credentials?project=piscale-calorie-minder
from __future__ import print_function

__author__ = "richard.james.kirby@gmailcom Richard Kirby"

import sys
import time
import datetime
import json
import sqlite3 as sql
import pathlib
from datetime import datetime
import threading
import logging
from socket import gaierror

logger = logging.getLogger("scaleLogger")

from oauth2client import client
from googleapiclient import sample_tools

mod_path = pathlib.Path(__file__).parent

# Class to connect to Google Fit to get calorie and other information.
class GoogleFitIf(threading.Thread):
    def __init__(self, argv):
        threading.Thread.__init__(self)

        # Default start time, beginning of Oct 2022.
        self.start_time = "1664582400000000000"
        self.argv = argv

        # Connect to the DB.
        self.calories_spent_db = sql.connect(f'{mod_path}/calories_spent.db', check_same_thread=False)

        # Create the Calorie Spent DB table if not already created. This table stores the calories expended by the
        # user through exercise and normal body functions such as breathing.
        with self.calories_spent_db:

            # create cursor object - this part is to create the initial table if it doesn't exist yet.
            cur = self.calories_spent_db.cursor()

            list_of_tables = cur.execute(
                """SELECT name FROM sqlite_master WHERE type='table'
                AND name='CaloriesSpent'; """).fetchall()

            # print(list_of_tables)
            if list_of_tables == []:
                print("Table not found, creating CaloriesSpent")

                # Create the table as it wasn't found.
                self.calories_spent_db.execute(""" CREATE TABLE CaloriesSpent(
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        StartNs INTEGER,
                        EndNs INTEGER,
                        StartDateTime TEXT,
                        EndDateTime TEXT,
                        Calories FLOAT
                        );
                    """)

                # Start time 01/10/2022 to be used if no database.
                self.start_time = "1664582400000000000"

            else: # Get the all the data from the database.
                # Read all the records
                self.calorie_history_data = self.calories_spent_db.execute("SELECT * FROM CaloriesSpent")
                for record in self.calorie_history_data:
                    #print(record)

                    # Start time is changed to ask for data based on the last record in the database.
                    self.start_time = str(record[2])

        self.service, self.flags = None, None

    # Provide database records to the caller. num_records of 0 will return all records.
    def return_records(self, num_records=0):
        self.calorie_history_data = self.calories_spent_db.execute("SELECT * FROM CaloriesSpent")

        ret_list = []

        for item in self.calorie_history_data:
            #print(item)
            ret_list.append(item)

        if num_records == 0:
            return ret_list
        else:
            return ret_list[:-num_records]

    # Thread main processing, kicked off by start. This loops through and gets fresh data after a delay each time.
    def run(self):

        logger.info("Google If run() function start")
        while(True):
            data_set = self.start_time +  '-' + str(time.time_ns())

            try:

                # Authenticate and construct service.
                self.service, self.flags = sample_tools.init(
                    self.argv,
                    "fitness",
                    "v1",
                    __doc__,
                    __file__,
                    scope="https://www.googleapis.com/auth/fitness.activity.read",
                )

                logger.info(f"Service {self.service} Flags {self.flags}")

                '''
                data_sources = self.service.users().dataSources().list(userId='me').execute()
 
                for index, s in enumerate(data_sources['dataSource']):

                    #print(f"\n\ndata stream-->{s['dataStreamId']}")
                    dataset = self.service.users().dataSources(). \
                        datasets(). \
                        get(userId='me', dataSourceId=s['dataStreamId'], datasetId=data_set). \
                        execute()

                active_minutes = self.service.users().dataSources(). \
                        datasets(). \
                        get(userId='me', dataSourceId='derived:com.google.active_minutes:com.google.android.gms: merge_active_minutes', datasetId=data_set). \
                        execute()
                '''

                calories_expended = self.service.users().dataSources(). \
                    datasets(). \
                    get(userId='me',
                        dataSourceId='derived:com.google.calories.expended:com.google.android.gms:merge_calories_expended',
                        datasetId=data_set). \
                    execute()

            # Exception Handler for all issues, not just Token Refreshes
            except client.AccessTokenRefreshError:
                logger.error(
                    "Problem getting the data. It might be The credentials have been revoked or expired, please re-run"
                    "the application to re-authorize. May also be some other issue - read the response from Google."
                )

            except gaierror as err:
                logger.error(f"Socket gai error raised - try to keep working {err=}, {type(err)=}")

            # Generic Exception Handler. Just continue on, hoping that it is temporary.
            except Exception as err:
                logger.error(f"Unexpected {err=}, {type(err)=}")

            calorie_records =[]

            logger.info(f"Calories Expended {calories_expended}")

            # Go through all the records of all calories expended via exercise or just breathing, etc.
            # Note that the calories expended is often empty.
            for item in calories_expended['point']:

                # Getting some values for use in later calculations, specifically to deal with calorie records
                # that split across a day.
                start = datetime.fromtimestamp(int(item['startTimeNanos'][:-9]))
                sec_day_start = int(item['startTimeNanos'][:-9]) % (60 * 60 * 24)

                end = datetime.fromtimestamp(int(item['endTimeNanos'][:-9]))
                sec_day_end = int(item['endTimeNanos'][:-9]) % (60 * 60 * 24)

                calories = float(item['value'][0]['fpVal'])

                # Split calories if crosses between dates. In this case the seconds between the end time and the beginning
                # of the day will be smaller than the start time.
                if sec_day_end < sec_day_start:
                    # Split calories according to num of seconds in the time range.
                    calories_day1 = ((60*60*24)- sec_day_start)/((60*60*24)- sec_day_start + sec_day_end) * calories
                    calories_day2 = calories - calories_day1

                    # Calculate the start of day 2 in sec by using int division to truncate. I.e. 00:00:00 of Day 2.
                    # Subtract one second to create the end time for day 1. i.e. 23:59:59
                    day2_start_s = int(int(item['endTimeNanos'][:-9]) / (60 * 60 * 24)) * (60 * 60 * 24)
                    day1_end_datetime = datetime.fromtimestamp(day2_start_s - 1)

                    # Create the record for day 1
                    calories_record_day1 = [item['startTimeNanos'], item['endTimeNanos'], start, day1_end_datetime, calories_day1]
                    calorie_records.append(calories_record_day1)

                    # Create day 2 record by going from 00:00 to the end time
                    day2_start_datetime = datetime.fromtimestamp(day2_start_s)
                    calories_record_day2 = [item['startTimeNanos'], item['endTimeNanos'], day2_start_datetime, end, calories_day2]
                    calorie_records.append(calories_record_day2)

                else: # Otherwise the calories don't have to be spread across 2 days, so just assign to the day.
                    calories_record = [item['startTimeNanos'], item['endTimeNanos'], start, end, calories]
                    calorie_records.append(calories_record)

            # Write new records.
            with self.calories_spent_db:

                for record in calorie_records:
                    # print(record)
                    self.calories_spent_db.execute(
                        "INSERT INTO CaloriesSpent (StartNs, EndNs, StartDateTime, EndDateTime, Calories) values(?, ?, ?, ?, ?)"
                        , [record[0], record[1], record[2], record[3], record[4]])
                    self.start_time = record[1]
                    logger.info(record)

            # Wait to avoid too much interaction with Google
            time.sleep(60*5)


if __name__ == "__main__":
    google_fit_if = GoogleFitIf(sys.argv)
    google_fit_if.start()