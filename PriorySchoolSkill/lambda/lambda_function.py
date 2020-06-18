# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import ask_sdk_core.utils as ask_utils
import datetime
from datetime import datetime, date, timedelta
import fuzzywuzzy
from fuzzywuzzy import fuzz 
from fuzzywuzzy import process 
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name, get_slot_value
from ask_sdk_model.ui import SimpleCard

from ask_sdk_model import Response

import boto3
from boto3.dynamodb.conditions import Key
import random

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LaunchRequestHandler(AbstractRequestHandler):
    
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Welcome to Priory School, say help to learn what I can do."
        return CommonStaticMethods.get_text_and_speach_output(speak_output,handler_input)


class CommonStaticMethods:
    @staticmethod
    def get_dynamodb_handle():
        sts_client = boto3.client('sts')
        assumed_role_object=sts_client.assume_role(RoleArn="arn:aws:iam::162360892116:role/PriorySchoolAlexaToDynamoDB", 
            RoleSessionName="AssumeRoleSession1")
        credentials=assumed_role_object['Credentials']

        dynamodb = boto3.resource('dynamodb', region_name='us-west-1',
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'])
        return dynamodb
    
    @staticmethod
    def lookup_dynamoDB(key):
        dynamodb = CommonStaticMethods.get_dynamodb_handle()
        table = dynamodb.Table('Events')
        print("##################################################")
        print(f"Looking up {key} in Events Table")
        print("##################################################")
        resp = table.query(KeyConditionExpression=Key('Key').eq(key))
        print("Found " + str(resp) + "from looking up " + key + "in table")
        print("##################################################")

        items = resp['Items']

        ## Sort array by Starttime as the key
        items = sorted(items, key=lambda item: item['StartTime'])


        # type: (HandlerInput) -> Response
        return items
        
    @staticmethod
    def get_all_items_from_dynamoDB(name):
        dynamodb = CommonStaticMethods.get_dynamodb_handle()
        table = dynamodb.Table(name)
        items = table.scan()
        return items
    
    @staticmethod
    def item_to_string(item):
        if(item["BeginDay"] == item["EndDay"]):
            return item["Name"] + " is on " + item["Date"]
        else:
            return item["Name"] + " is from " + item["Date"] + " to " + item["EndTime"]
    
    @staticmethod
    def join_list(L):
        output = ""
        if len(L)>2:
            output =  ', '.join(L[:-1]) + ", and " + str(L[-1])
        elif len(L)==2:
            output =  ' and '.join(L)
        elif len(L)==1:
            output =  L[0]
        return output
    
    @staticmethod
    def get_current_date():
        now_pst = datetime.now() - timedelta(hours = 7)
        today = now_pst.date()
        print("The date today is " + str(today))
        return today
        
    
    def get_text_and_speach_output(speak_output,handler_input):
        return handler_input.response_builder.speak(speak_output).set_card(
            SimpleCard("TITLE", speak_output)).response
        
    
class PrioryEventsIntentHandler(AbstractRequestHandler):
    """Handler for PrioryEventsIntent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("PrioryEventsIntent")(handler_input)

    def handle(self, handler_input):
        print("calling PrioryEventsIntentHandler")
        print("handler input is " + str(handler_input.request_envelope.request.intent))
        key = get_slot_value(handler_input=handler_input, slot_name="day")
        print(f"key is {key}")
        outputs = CommonStaticMethods.lookup_dynamoDB(key)
        len_outputs = len(outputs)
        outputs = [item["Name"] for item in outputs]
        if len_outputs  == 1:
            speak_output = f"The only event on this day is {outputs[0]}"
        if len_outputs > 1:
            speak_output = f"There are {str(len_outputs)} events on this day. They are {CommonStaticMethods.join_list(outputs)}"
        if len_outputs == 0:
            #TODO: say something different if today is this date
            speak_output = "There are no events on this day"
            
        card_title = "Events on this day"
        card_text = speak_output

        print("##################################################")
        print("Voice output from PrioryEventsIntentHandler is "  + str(speak_output))
        print("##################################################")
       # speak_output = "Working."

        return CommonStaticMethods.get_text_and_speach_output(speak_output, handler_input)
    
    
class PrioryDayOfEventIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("PrioryDayOfEventIntent")(handler_input)
        
    def get_matches(self, items, priory_event):
        matches = [];
        absolute_matches = []
        absolute_match = False
        for item in items["Items"]:
            word_ratio = fuzz.token_set_ratio(item["Name"], priory_event)
            if word_ratio > 60:
                matches.append([item, word_ratio])
                if(word_ratio == 100):
                    absolute_match = True
                    absolute_matches.append([item, word_ratio])
        
        if absolute_match:
            matches = absolute_matches
            
        matches.sort(key=lambda x: str(100 - x[1]) + x[0]["Date"])
        matches = [item[0] for item in matches]
        
        return matches
        
    def handle(self, handler_input):
        print("calling DayOfEventIntentHandler")
        print("handler input is " + str(handler_input))
        priory_event = get_slot_value(handler_input=handler_input, slot_name="prioryEvent")
        print("PrioryDayOfEventIntentHandler input: " + priory_event)
        items = CommonStaticMethods.get_all_items_from_dynamoDB('Events')
        
        matches = self.get_matches(items, priory_event)

        today = CommonStaticMethods.get_current_date()
        
        output = []
        for item in matches:
            if item["DayTypeEvent"]:
                if item["BeginDay"] and datetime.strptime(item["EndTime"],'%Y-%m-%d').date() >= today:
                    output.append(item)
            else:
                output.append(item)
        outputs = [CommonStaticMethods.item_to_string(item) for item in output]
        
        if (len(outputs) == 0):
            speak_output = "I could not find any events matching " + priory_event
        else:
            speak_output = CommonStaticMethods.join_list(outputs)

        return CommonStaticMethods.get_text_and_speach_output(speak_output, handler_input)



class WeekIntentHandler(AbstractRequestHandler):
    """Handler for WeekIntent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("PrioryWeekIntent")(handler_input)

    def handle(self, handler_input):
        print("calling WeekIntentHandler")
        print("handler input is " + str(handler_input))
        today = date.today()
        key = str(today.year) + "-W" + today.strftime("%U")
        
        outputs = CommonStaticMethods.lookup_dynamoDB(key)
        if len(outputs) > 0:
            speak_output = "This week is a " + outputs[0]["Name"]
        else:
            speak_output = "This week doesn't have a week type"
        
        
        print("***##################################################")
        print("Voice output from WeekIntentHandler is " + speak_output)
        print("***##################################################")

        return CommonStaticMethods.get_text_and_speach_output(speak_output)
    

class PrioryRandomFactIntentHandler(AbstractRequestHandler):
    
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("PrioryRandomFactIntent")(handler_input)
        
    
    def handle(self, handler_input):
        print("called handle method in PrioryrandomFactIntent")
        items = CommonStaticMethods.get_all_items_from_dynamoDB('Facts')
        speak_output = (random.choice(items["Items"]))["Fact"]
        return CommonStaticMethods.get_text_and_speach_output(speak_output, handler_input)
    
    
    
class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = """Here are four things I can do:
        Number one, you can ask me for a random Priory fact.
        Number two, you can ask what is happening on a given day.
        Number three, you can ask when a given event happens.
        number four, you can ask for the current week's schedule."""

        return CommonStaticMethods.get_text_and_speach_output(speak_output, handler_input)


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(PrioryEventsIntentHandler())
sb.add_request_handler(PrioryDayOfEventIntentHandler())
sb.add_request_handler(WeekIntentHandler())
sb.add_request_handler(PrioryRandomFactIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()