import json
import boto3
from icalendar import Calendar, Event
from datetime import datetime, date, timedelta
import re
import os
import requests
import pprint
import pickle



PICKLE_FILE = "/tmp/ical_events.p"

class CalendarEventExtractor:
    DEBUG = False
    iCAL_FILE = '/tmp/CalExport.ics'
    iCAL_URL = "http://prioryca.myschoolapp.com/podium/feed/iCal.aspx?z=Hf9edo%2f1PGOjXbQJR%2fxGnW0hsfmohamUcVyp%2bMgFNkYxemJMI%2b4S%2b5FBY64hvnM50mhox1fBNLvmn05hgQZW5IemsBgScSjkHfW9yajHfssbMc7yDlPcVbe0XZFdyJUVhxt4NAZ41rZQLM0wuoF4O9%2bWeYMqp9rUvBuwNrfWLgU%2bsxqdtbVhOhW8R9sLBBNeezcTiMBRDlCiItO43S%2byp%2bx3QjTv6haLtg8Q5FW10ASaDmQeH7WzO8pTTS4RlqChXcsm9C%2foNDRbMcXRE1FFjg8AWqfCeEk13VIxRVvszEgPkc1eNLbEz%2bvwqFCsX4sgUbpJKwBvOpEd6HkHtZ%2bpfw%3d%3d"
    HTTP_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
 
    """"
    This class will allow you to fetch the calendar information 
    from a website and then convert it into a dictionary.
    
    Attributes:
        url: the url from which the information is read from
        filename: the file which the information is written into
    """

    def __init__(self, filename=iCAL_FILE, url=iCAL_URL, debug=DEBUG):
        self.ical_file = filename
        self.ical_url = url
        self.out = []
        self.debug = debug
        self.ical_content = None
        

    def get_ical_file(self):
        """
        This method downloads the calendar information from 
        the Priory website then writes it to a file
        """
        r =  requests.get(self.ical_url, 
                          headers=CalendarEventExtractor.HTTP_HEADERS, 
                          allow_redirects=True)
        self.ical_content = r.content
    
    
    def _convert_to_week_format(self, date_dt):
        """"This method takes a date time object and returns a work week string"""
        return str(date_dt.year) + "-W" +  str(date_dt.isocalendar()[1])
    
    
    def _debug(self, summary, dtstart_dt, 
               dtend_dt, duration_dt, status, class_str):
         if self.debug:
                    print("DEBUG START: ---------------------------------")
                    print('summary: ', summary)
                    print('dtstart_dt: ', dtstart_dt)
                    print('dtend_dt: ', dtend_dt)
                    print('duration_dt: ', duration_dt)
                    print('status: ',status)
                    print('class_str: ', class_str)
                    print("DEBUG END: -----------------------------------")
    
    def _get_event_attributes(self, event):
        summary = event.get('summary').to_ical().decode("utf-8")
        status = event.get('status').to_ical().decode("utf-8")
        class_str = event.get('class').to_ical().decode("utf-8")
        dtstart_dt = event.get('dtstart').dt
        dtend_dt = event.get('dtend').dt
        return [summary, status, class_str, dtstart_dt, dtend_dt]
    
    def process_event(self, event):
        if event.name == "VEVENT":
                [summary, status, class_str, 
                 dtstart_dt, dtend_dt] = self._get_event_attributes(event)
            
                duration_dt = dtend_dt - dtstart_dt
           
                self._debug(summary, dtstart_dt, dtend_dt, 
                            duration_dt, status, class_str)

                if status == "CONFIRMED" and class_str == "PUBLIC":
                    [day_type_event, date_dt, 
                     start_time_str, end_time_str,
                     date_dt_str] = self._rename_me_correctly(dtstart_dt,
                                                              dtend_dt, duration_dt)

                    
                    self._unroll_and_append_events(duration_dt, summary, 
                                  date_dt, dtstart_dt, date_dt_str, start_time_str,
                                  end_time_str, day_type_event)


    def _rename_me_correctly(self, dtstart_dt, dtend_dt, duration_dt):
        day_type_event = None
        if callable(getattr(dtstart_dt, "date", None)):
            day_type_event = False
            date_dt = dtstart_dt.date()
            start_time_str = dtstart_dt.strftime("%H:%M:%S")
            end_time_str = dtend_dt.strftime("%H:%M:%S")
        else:
            day_type_event = True
            date_dt = dtstart_dt
            start_time_str = date_dt.isoformat()
            end_time_str = (date_dt + duration_dt - timedelta(days = 1)).isoformat();
                
        date_dt_str = date_dt.isoformat()
            
        return [day_type_event, date_dt, 
            start_time_str, end_time_str,
            date_dt_str]
                
    def _unroll_and_append_events(self, duration_dt, summary, 
                                  date_dt, dtstart_dt, date_dt_str, start_time_str,
                                  end_time_str, day_type_event):
        max_days = max(duration_dt.days, 1)
        for x in range(max_days):
            if re.match("[A|B|C] Week", summary):
                key_str = _convert_to_week_format(date_dt)
            else:
                key_str = date_dt.isoformat()
                        
            begin_day = (x == 0)
            end_day = (x == (max_days - 1))
                    
            item = {"Key": key_str, "Name": summary, 
                    "Date": date_dt_str, "StartTime": start_time_str, 
                    "EndTime": end_time_str, "BeginDay": begin_day, 
                    "EndDay": end_day, "DayTypeEvent": day_type_event}
            date_dt = date_dt + timedelta(days = 1)
            date_dt_str = dtstart_dt.isoformat()
            self.out.append(item)
                    
    
    
    def get_events(self):
        self.out = []
        calendar = Calendar.from_ical(self.ical_content)
        for event in calendar.walk():
            self.process_event(event)
        return self.out
        
    def pretty_print_events(self):
        pp = pprint.PrettyPrinter(indent = 4)
        for item in self.out:
            pp.pprint(item)
            
    def make_pickle(self):
        """Makes a pickle file of the calendar events"""
        pickle.dump(self.out, open(PICKLE_FILE, "wb"))


class PopulateDynamoDBEventTable:
    """"
    This class will populate the DynamoDB from a list of events. 
    It will delete events which no longer appear on the event list.
    It will add new events and update existing events
    
    Attributes:
        events: A list of all events appearing on the calendar. 
        Each event takes the form of a dictionary. If events is not supplied, 
        it will load events from the pickle file
    """
    RUN_CODE_LOCAL = False
    USE_PRODUCTION_DB = True

    def __init__(self, events=False):
        self.set_dynamo()
        if not events:
            self.events = pickle.load(open(PICKLE_FILE, "rb"))
        else:
            self.events = events
        self.items_in_dynamoDB = None
    
    def set_dynamo(self):
        if PopulateDynamoDBEventTable.USE_PRODUCTION_DB:
            if(PopulateDynamoDBEventTable.RUN_CODE_LOCAL):
                self.set_dynamo_local_and_production_db()
            else:
                self.set_dynamo_lambda_and_production_db()
        else:      
            self.set_dynamo_local_and_local_db()  
        
    def set_dynamo_local_and_production_db(self):
        self.dynamodb = boto3.resource('dynamodb',
            aws_access_key_id=os.environ["DYNAMODB_ID"],
            aws_secret_access_key=os.environ["DYNAMODB_KEY"],
            region_name='us-west-1')
        
        
    def set_dynamo_lambda_and_production_db(self):

        self.dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
                
                
    def set_dynamo_local_and_local_db(self):
        self.dynamodb = boto3.resource('dynamodb',
                                           aws_access_key_id="fakeMyKeyId",
                                           aws_secret_access_key="fakeSecretAccessKey",
                                           region_name='us-west-1',
                                           endpoint_url='http://localhost:8000')
          
    
    def pretty_print_old_events_in_dynamoDB(self):
        pp = pprint.PrettyPrinter(indent = 4)
        for item in self.items_in_dynamoDB['Items']:
            pp.pprint(item)
    
    def delete_absent_events_from_dynamoDB(self):
        delete_count = 0
        table = self.dynamodb.Table('Events')
        for item in self.items_in_dynamoDB["Items"]:
            if(not item in self.events):
                table.delete_item(
                   Key = {"Key": item["Key"],
                          "Name": item["Name"]})
                delete_count += 1
                #print(str(item) + " has been deleted")
        print(f"{delete_count} items from DynamoDB have been deleted.")

  
    def populate_dynamoDB(self):
        table = self.dynamodb.Table('Events')
        # The BatchWriteItem API allows us to write multiple items to a table in one request.
        with table.batch_writer() as batch:
            for event in self.events:
                batch.put_item(Item=event)

        # We need to delete entries in DynamoDB that are no longer present 
        # in Priory calendar
        self.items_in_dynamoDB = table.scan() 
        print(f"Found {len(self.items_in_dynamoDB['Items'])} items in DynamoDB Events Table.")
        
        self.delete_absent_events_from_dynamoDB()



def prioryEventsPeriodicLambda(event, context):
    pm = CalendarEventExtractor()
    pm.get_ical_file()
    print("Downloaded calendar from website.")
    events = pm.get_events()
    #pm.pretty_print_events()
    print(f"Got {len(events)} applicable calendar events.")
    pd = PopulateDynamoDBEventTable(events)
    pd.populate_dynamoDB()
    print("Populated DynamoDB")
