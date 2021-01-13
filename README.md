### Alexa Skill for Woodside Priory High School

This is an Alexa skill that I made for my senior project at Woodside Priory High School. It allows the user to ask about calendar events such as the dates for certain events and the events for certain dates as well as the particular week schedule. The skill also allows the user to ask for random facts about Priory. 

The Weebly blog is [here](https://prioryalexa.weebly.com/)

The Vimeo project presentation is [here](https://vimeo.com/423808312)

The Google Slide presentation is [here](The Vimeo project presentation [here](https://vimeo.com/423808312)

To create a zip file that can be uploaded to AWS Lambda:


    python3 -m venv v-env
    source v-env/bin/activate
    pip install icalendar
    pip install datetime
    pip install re
    pip install requests
    pip install pprint
    cd v-env/lib/python3.7/site-packages/
    zip -r9 ../../../../prioryEventsPeriodicLambda.zip .
    zip -g prioryEventsPeriodicLambda.zip prioryEventsPeriodicLambda.py
