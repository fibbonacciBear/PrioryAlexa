Alexa Skill for Priory


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
