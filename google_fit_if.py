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
import sqlite3 as sql
import pathlib
import threading
import logging.config
from socket import gaierror

from oauth2client import client
from googleapiclient import sample_tools

logging.config.fileConfig('logging.conf')
glogger = logging.getLogger('googleifLogger')
glogger.setLevel(logging.DEBUG)
print(glogger)

mod_path = pathlib.Path(__file__).parent

# Class to connect to Google Fit to get calorie and other information.
class GoogleFitIf(threading.Thread):
    def __init__(self, argv):
        threading.Thread.__init__(self)

        glogger.info(f"{__name__} Google If __init__")

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
                    # ToDo: there might be an easier way of doing this. A SQLquery is likely to be faster.
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
            return ret_list[-num_records:]

    # Thread main processing, kicked off by start. This loops through and gets fresh data after a delay each time.
    def run(self):


        glogger.info(f"{__name__} Google If run() function start")
        while(True):

            # Get today's date for a later query.
            today = datetime.date.today().strftime("%Y-%m-%d")
            # print(int(today[0:4]), int(today[5:7]), int(today[8:10]))
            # print(today, datetime.datetime(int(today[0:4]), int(today[5:7]), int(today[8:10])).timestamp())

            '''
            # Gives us date time for our timezone
            start_of_my_day = datetime.datetime(int(today[0:4]), int(today[5:7]), int(today[8:10])).\
                replace(tzinfo=datetime.timezone.utc).timestamp()

            # Gives us date time for our timezone
            start_of_my_day2 = datetime.datetime(int(today[0:4]), int(today[5:7]), int(today[8:10])).timestamp()

            print(f"start of my day: {start_of_my_day2}")
            ''' 
            # Calculate the day start in nanoseconds
            day_start_ns = str(datetime.datetime(int(today[0:4]), int(today[5:7]), int(today[8:10])).timestamp())[:-2] \
                           + '000000000'
            #print(day_start_ns)


            # Find all records from today

            # Query for today's records -
            # today_records = self.calories_spent_db.execute(
            #                "SELECT id, StartDateTime, EndDateTime FROM CaloriesSpent WHERE date(StartDateTime)= ?",
            #                (today,))
            # for record in today_records:
            #    print(record)



            # Delete all records from today - it doesn't work very well to collect over the records over the same day.
            # Get odd results - not clear if Google Fit is causing the problem or this code.
            del_cursor = self.calories_spent_db.execute("DELETE FROM CaloriesSpent WHERE date(EndDateTime)= ?",
                                                        (today,))

            # Delete the last record as it normally splits over midnight
            del_last_record_cursor1=self.calories_spent_db.execute("DELETE FROM CaloriesSpent ORDER BY id DESC LIMIT 1")

            # Delete the last record as it normally splits over midnight
            del_last_record_cursor2=self.calories_spent_db.execute("DELETE FROM CaloriesSpent ORDER BY id DESC LIMIT 1")

            # Commit to finalise the deletions.
            self.calories_spent_db.commit()

            glogger.info(f"Number of records deleted from today EndDate {today} {del_cursor.rowcount} "
                        f"and last two {del_last_record_cursor1.rowcount + del_last_record_cursor2.rowcount}")

            # Get the new last record in the database (after deleting everything from today)
            last_record = self.calories_spent_db.execute(
                "SELECT * FROM CaloriesSpent ORDER BY id DESC LIMIT 1").fetchone()

            # glogger.info(f"fetch one **{last_record.fetchone()}")

            # Get the start time based on the last record's End Time in nanoseconds. It is the 3rd field in the record.
            # If no records, then the default start time will be used as per the __init__.
            if last_record is not None:
                self.start_time = int(last_record[2])

            else: # No change.
                self.start_time = self.start_time

            end_time_ns = time.time_ns()

            glogger.info(f"Using start time/end time as "
                        f"{self.start_time} {datetime.datetime.fromtimestamp(int(self.start_time)/1000000000)} / "
                        f"{end_time_ns} {datetime.datetime.fromtimestamp(int(end_time_ns/1000000000))}")

            data_set = str(self.start_time) +  '-' + str(end_time_ns)


            try:
                calories_expended = None

                glogger.info(f"Setting up Google IF. Data Set {data_set}")
                # Authenticate and construct service.
                self.service, self.flags = sample_tools.init(
                    self.argv,
                    "fitness",
                    "v1",
                    __doc__,
                    __file__,
                    scope="https://www.googleapis.com/auth/fitness.activity.read",
                )

                glogger.info(f"Service {self.service} Flags {self.flags}")

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
                glogger.error(
                    "Problem getting the data. It might be The credentials have been revoked or expired, please re-run"
                    "the application to re-authorize. May also be some other issue - read the response from Google."
                )

            except gaierror as err:
                glogger.error(f"Socket gai error raised - try to keep working {err=}, {type(err)=}")

            # Generic Exception Handler. Just continue on, hoping that it is temporary.
            except Exception as err:
                glogger.error(f"Unexpected {err=}, {type(err)=}")

            except:
                glogger.error("unprocessed exception")

            calorie_records =[]

            glogger.info(f"Calories Expended {calories_expended}")

            # Go through all the records of all calories expended via exercise or just breathing, etc.
            # Note that the calories expended is often empty.
            if calories_expended is not None:
                for item in calories_expended['point']:

                    # Convert start time seconds to a date and time
                    start_time_s = int(item['startTimeNanos'][:-9])
                    start = datetime.datetime.fromtimestamp(start_time_s) # in timezone

                    # Convert end time seconds to a date and time
                    end_time_s = int(item['endTimeNanos'][:-9])
                    end = datetime.datetime.fromtimestamp(end_time_s) # in timezone

                    # Calculate the difference between UTC and the timezone.
                    start_utc = datetime.datetime.utcfromtimestamp(start_time_s)  # UTC time
                    utc_diff = str(start-start_utc).split(':') # to calculate timezone shift
                    utc_diff_in_sec = int(utc_diff[0])* 60 * 60 # + int(utc_diff[1])/60.0 * 60 * 60

                    # Calculate the difference in days between start and end times. Should be 0 for same day, 1 for
                    # a record that spans a day.
                    start_day_days_since_epoch = int(start_time_s/ (60 * 60 * 24))
                    end_day_days_since_epoch = int(end_time_s / (60 * 60 * 24))

                    diff_days_end_start = end_day_days_since_epoch - start_day_days_since_epoch

                    calories = float(item['value'][0]['fpVal'])

                    #glogger.info(f"{start_day_days_since_epoch} {end_day_days_since_epoch} "
                    #            f"diff_days_end_start {diff_days_end_start} "
                    #            f"/Start/End/Calories {start_time_s} {end_time_s}/{calories}")

                    # Split calories if crosses between date if the record spans a date.

                    if diff_days_end_start != 0:
                        # Calculate how long between start time and the end of its day.
                        start_time_to_day_end = 24 * 60 * 60 - (start_time_s % (24 * 60 * 60))

                        glogger.info(f"start_time_to_day_end {start_time_to_day_end}")

                        # Split calories according to num of seconds in the time range. Ratio will be the time
                        # between the end of the start day and the end of its day and the whole range.
                        calories_day1 = float(start_time_to_day_end/ (end_time_s - start_time_s)) *calories

                        calories_day2 = calories - calories_day1

                        # Calculate the start of day 2 in sec by using int division to truncate. I.e. 00:00:00 of Day 2.
                        # Subtract one second to create the end time for day 1. i.e. 23:59:59
                        day2_start_s = int(end_time_s / (60 * 60 * 24)) * (60 * 60 * 24) \
                                       - utc_diff_in_sec
                        day1_end_datetime = datetime.datetime.fromtimestamp(day2_start_s - 1)

                        # Create the record for day 1
                        calories_record_day1 = [item['startTimeNanos'], (day2_start_s -1) * 1000000000, start,
                                                day1_end_datetime, calories_day1]
                        calorie_records.append(calories_record_day1)

                        # Create day 2 record by going from 00:00 to the end time
                        day2_start_datetime = datetime.datetime.fromtimestamp(day2_start_s)
                        calories_record_day2 = [day2_start_s * 1000000000, item['endTimeNanos'], day2_start_datetime,
                                                end, calories_day2]

                        calorie_records.append(calories_record_day2)
                        glogger.info(f"calories_record_day1 {calories_record_day1} "
                                    f"calories_record_day2 {calories_record_day2}")

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
                        glogger.info(record)

            # Wait to avoid too much interaction with Google
            time.sleep(60*13)


if __name__ == "__main__":
    google_fit_if = GoogleFitIf(sys.argv)
    google_fit_if.start()