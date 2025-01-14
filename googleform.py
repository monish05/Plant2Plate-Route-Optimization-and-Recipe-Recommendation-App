import pandas as pd
import requests
import copy
import numpy as np
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pickle
import json


class ExcelExtraction():
    
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        self.SPREADSHEET_ID = 'ENTER SPREADSHEET LINK'
        self.RANGE_NAME = 'Form Responses 1!A1:I'
        
    def get_credentials(self):
        """Log in to the Google API and save the session for future use."""
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return creds
    
    def main(self):
        """Shows basic usage of the Sheets API.
        Prints values from a sample spreadsheet.
        """
        creds = self.get_credentials()
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=self.SPREADSHEET_ID,
                                    range=self.RANGE_NAME).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
        else:
            # Convert to JSON
            data = []
            headers = values[0]  # Assumes first row is headers
            for row in values[1:]:  # Skip header row
                entry = {headers[i]: row[i] for i in range(len(row))}
                data.append(entry)
            json_data = json.dumps(data, indent=4)
            final = json.loads(json_data)
            return final
        
        
class ExcelConversation():
    def __init__(self, campusId):
        self.data_extraction = ExcelExtraction()
        self.campusId = campusId

        
    def getData(self):
        data = self.data_extraction.main()
        final_list = {}
        for i in data:
            dict_cr = {}
            fcId = 0
            for j in i:
                if "Campus" in j:
                    cId = int(i[j])
                    if cId not in final_list:
                        final_list[cId] = []
                        fcId = cId
                if "Check" in j:
                    dow = j.split("[")[1][:-1]
                    if dow not in dict_cr:
                        dict_cr[dow] =  i[j].split(',')

            check_day = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            for k in dict_cr:
                if k in check_day:
                    check_day.remove(k)


            for l in check_day:
                if l not in dict_cr:
                    dict_cr[l] = []

            if fcId != 0:        
                final_list[fcId].append(dict_cr)
                
        return final_list
    
    def excelToPandas(self):
        result = {}
        final_list = self.getData()
        campusId = self.campusId
        for i in final_list[campusId][-1]:
            tl = []
            for j in final_list[campusId][-1][i]:
                time_period = j.strip()
                # Parse the start and end times
                start_time_str, end_time_str = time_period.replace('am', ' AM').replace('pm', ' PM').split('-')

                # Convert to time objects
                start_time = datetime.strptime(start_time_str, '%I %p').time()
                end_time = datetime.strptime(end_time_str, '%I %p').time()

                tl.append([start_time, end_time])
            if i not in result:
                result[i] = tl

        df = pd.DataFrame({"DOW" : list(result.keys()),
                     "Time" : list(result.values())})      
        df = df.explode('Time')

        df['idx'] = df.groupby('DOW').cumcount()

        pivoted_df = df.pivot(index='idx', columns='DOW', values='Time')

        return pivoted_df
    
    def extractingGaps(self):
        df = self.excelToPandas()
        time = ["7am-8am", "8am-9am" , "9am-10am", "10am-11am", "11am-12pm", "12pm-1pm", "1pm-2pm", "2pm-3pm", "3pm-4pm", "4pm-5pm", "5pm-6pm", "6pm-7pm", "7pm-8pm", "8pm-9pm", "9pm-10pm"]
        tl = []

        for i in time:
            time_period = i.strip()
            # Parse the start and end times
            start_time_str, end_time_str = time_period.replace('am', ' AM').replace('pm', ' PM').split('-')

            # Convert to time objects
            start_time = datetime.strptime(start_time_str, '%I %p').time()
            end_time = datetime.strptime(end_time_str, '%I %p').time()

            tl.append([start_time, end_time])


        free_time = {}
        day_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for i in day_list:
            time_list = copy.deepcopy(tl)
            for j in df[i]:
                if j in time_list:
                    time_list.remove(j)
            if i not in free_time:
                free_time[i] = time_list

        return free_time
    
    def getMergeTimeHelper(self, times):
        combined_times = []
        start_time = None
        end_time = None
        for time_range in times:
            if time_range is np.nan:
                continue
            if start_time is None:
                start_time = time_range[0]
                end_time = time_range[1]
            elif end_time == time_range[0]:
                end_time = time_range[1]
            else:
                combined_times.append([start_time, end_time])
                start_time = time_range[0]
                end_time = time_range[1]
        if start_time is not None and end_time is not None:
            combined_times.append([start_time, end_time])
        return combined_times
    
    def getMergeTime(self):
        schedule = self.extractingGaps()
        combined_schedule = {day: self.getMergeTimeHelper(times) for day, times in schedule.items()}

        combine_dict = {}
        for day, times in combined_schedule.items():
            if day not in combine_dict:
                combine_dict[day] = times

        return combine_dict
    
    def getFreeTimes(self):
        
        merge_time_dict = self.getMergeTime()
        new_schedule_data = []

        for day, times in merge_time_dict.items():
            for time_slot in times:
                if time_slot is not None:
                    start_time, end_time = time_slot
                    datetime1 = datetime.combine(datetime.today(), start_time)
                    datetime2 = datetime.combine(datetime.today(), end_time)
                    time_difference = datetime2 - datetime1

                    duration = str(int(time_difference.total_seconds() / 3600)) + 'hrs'
                    new_schedule_data.append([day, f"{start_time}-{end_time}", duration])

        new_schedule_df = pd.DataFrame(new_schedule_data, columns=['Day', 'Time Slot', 'Duration'])

        return new_schedule_df

