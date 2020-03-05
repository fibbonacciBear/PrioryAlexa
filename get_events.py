import requests
from icalendar import Calendar, Event
iCAL_URL = "http://prioryca.myschoolapp.com/podium/feed/iCal.aspx?z=Hf9edo%2f1PGOjXbQJR%2fxGnW0hsfmohamUcVyp%2bMgFNkYxemJMI%2b4S%2b5FBY64hvnM50mhox1fBNLvmn05hgQZW5IemsBgScSjkHfW9yajHfssbMc7yDlPcVbe0XZFdyJUVhxt4NAZ41rZQLM0wuoF4O9%2bWeYMqp9rUvBuwNrfWLgU%2bsxqdtbVhOhW8R9sLBBNeezcTiMBRDlCiItO43S%2byp%2bx3QjTv6haLtg8Q5FW10ASaDmQeH7WzO8pTTS4RlqChXcsm9C%2foNDRbMcXRE1FFjg8AWqfCeEk13VIxRVvszEgPkc1eNLbEz%2bvwqFCsX4sgUbpJKwBvOpEd6HkHtZ%2bpfw%3d%3d"
# Get iCal file:
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
r = requests.get(iCAL_URL, headers=headers, allow_redirects=True)
open('/tmp/CalExport.ics', 'wb').write(r.content)
# Open and process the iCal file
g = open('/tmp/CalExport.ics','rb')
gcal = Calendar.from_ical(g.read())
count = 0
for component in gcal.walk():
    if component.name == "VEVENT":
        count += 1
        print("---------------------------------")
        print(component.get('summary'))
        print(component.get('dtstart').to_ical())
        print(component.get('dtend').to_ical())
        print(component.get('CATEGORIES').to_ical())
g.close()
print(count)