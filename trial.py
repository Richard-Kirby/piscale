#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Simple command-line sample for Blogger.
Command-line application that retrieves the users blogs and posts.
Usage:
  $ python blogger.py
You can also get help on all the command-line flags the program understands
by running:
  $ python blogger.py --help
To get detailed log output run:
  $ python blogger.py --logging_level=DEBUG
"""
from __future__ import print_function

__author__ = "jcgregorio@google.com (Joe Gregorio)"

import sys
import time
import datetime
import json
import sqlite3 as sql
import pathlib
from datetime import datetime, timedelta
import threading

from oauth2client import client
from googleapiclient import sample_tools

mod_path = pathlib.Path(__file__).parent

class GoogleFitIf(threading.Thread):
    def __init__(self, argv):
        threading.Thread.__init__(self)
        self.start_time = "1664582400000000000"

        # Connect to the DB.
        self.calories_spent_db = sql.connect(f'{mod_path}/calories_spent.db', check_same_thread=False)

        print(self.calories_spent_db)

        # Create the Meal History DB tables if not already created.
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
                    print(record)

                    # Start time is changed to ask for data based on the last record in the database.
                    self.start_time = str(record[2])

        # Authenticate and construct service.
        self.service, self.flags = sample_tools.init(
            argv,
            "fitness",
            "v1",
            __doc__,
            __file__,
            scope="https://www.googleapis.com/auth/fitness.activity.read",
        )

    def run(self):

        while(True):
            data_set = self.start_time +  '-' + str(time.time_ns())

            try:

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

                calories_expended = self.service.users().dataSources(). \
                    datasets(). \
                    get(userId='me',
                        dataSourceId='derived:com.google.calories.expended:com.google.android.gms:merge_calories_expended',
                        datasetId=data_set). \
                    execute()

            except client.AccessTokenRefreshError:
                print(
                    "The credentials have been revoked or expired, please re-run"
                    "the application to re-authorize"
                )

            #for keys in calories_expended:
            #    print(keys)

            #print(calories_expended['point'])

            calorie_records =[]

            if (calories_expended != None):

                # Go through all the records of all calories expended via exercise or just breathing, etc.
                for item in calories_expended['point']:

                    #print(item)
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

                    else:
                        calories_day1 = calories
                        calories_day2 = 0

                        calories_record = [item['startTimeNanos'], item['endTimeNanos'], start, end, calories]
                        calorie_records.append(calories_record)


                    # print(start, sec_day_start, end, sec_day_end, calories, calories_day1, calories_day2)

                with self.calories_spent_db:

                    for record in calorie_records:
                        print(record)
                        self.calories_spent_db.execute(
                            "INSERT INTO CaloriesSpent (StartNs, EndNs, StartDateTime, EndDateTime, Calories) values(?, ?, ?, ?, ?)"
                            , [record[0], record[1], record[2], record[3], record[4]])
                        self.start_time = record[1]
                time.sleep(60*15)


if __name__ == "__main__":
    google_fit_if = GoogleFitIf(sys.argv)
    print(google_fit_if.start_time)
    google_fit_if.start()