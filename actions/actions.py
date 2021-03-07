from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from typing import Text, List, Any, Dict

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet, FollowupAction

import base64 
import smtplib, ssl
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ZomatoData = pd.read_csv('zomato.csv')
ZomatoData = ZomatoData.drop_duplicates().reset_index(drop=True)
WeOperate = {city.lower() for city in ZomatoData.City.unique()}

class ValidateRestaurantSearchForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_restaurant_search_form"

    def validate_location(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate location value."""
        
        if slot_value.lower() in WeOperate:
            # validation succeeded, set the value of the "location" slot to value
            return {"location": slot_value}
        else:
            dispatcher.utter_message(template="utter_not_available_location")
            
            FollowupAction(name = "action_listen")
            return {"location":None}

def RestaurantSearch(city, cuisine, budget=None):
    Restaurants = ZomatoData[ZomatoData.City.str.contains(city, case=False) & #Filter by city
                      ZomatoData.Cuisines.str.contains(cuisine, case=False)] #Filter by cuisine
    if len(Restaurants):
        Restaurants = Restaurants[['Restaurant Name','Address','Average Cost for two','Aggregate rating']]
        # Filter by budget
        # Sort by 'Aggregate rating'
        Restaurants = Restaurants.sort_values(by='Aggregate rating', ascending=False)
        # Return top 5
        return Restaurants.head(5)
    return 

class ActionSearchRestaurants(Action):
	def name(self):
		return 'action_search_restaurants'

	def run(self, dispatcher, tracker, domain):
		loc = tracker.get_slot('location')
		cuisine = tracker.get_slot('cuisine')
		results = RestaurantSearch(city=loc,cuisine=cuisine)
		response=""
		if results.shape[0] == 0:
			response= "no results"
		else:
			for restaurant in RestaurantSearch(loc,cuisine).iloc[:5].iterrows():
				restaurant = restaurant[1]
				response=response + F"Found {restaurant['Restaurant Name']} in {restaurant['Address']} rated {restaurant['Address']} with avg cost {restaurant['Average Cost for two']} \n\n"
				
		dispatcher.utter_message("-----"+response+"----- \n Is it useful?")
		return [SlotSet('location',loc)]

class ActionSendMail(Action):
	def name(self):
		return 'action_send_email'

	def run(self, dispatcher, tracker, domain):
		MailID = tracker.get_slot('email')
		loc = tracker.get_slot('location')
		cuisine = tracker.get_slot('cuisine')
		results = RestaurantSearch(city=loc,cuisine=cuisine)
		sendmail(MailID, results)
		dispatcher.utter_message("----Email has been sent----")
		return [SlotSet('email',MailID)]


def sendmail(mail_id, content):

    sender_email = "sandy.mymessage@gmail.com"
    receiver_email = mail_id
    passcode_bytes = base64.b64decode('U3kjQSZpNFU='.encode("ascii")) 

    message = MIMEMultipart("alternative")
    message["Subject"] = "Restaurant Search"
    message["From"] = sender_email
    message["To"] = receiver_email

    # Create the plain-text and HTML version of your message
    text = """\
    Hi,
    Hope you are doing Great!
    We thoungh these Restaurants will suit for you.:
    Thanks for using our service! Your reviews are valuable."""
    html = """\
    <html>
      <body>
        <p>Hi,<br>
           Hope you are doing Great!<br>
        </p>
        <h3>We thoungh these Restaurants will suit for you.
        <h3>"""+content.to_html(index=False)+"""</body>
        <p>Thanks for using our service! <br>
        Your reviews are Invaluable.</p>
    </html>"""

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)
    
    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, passcode_bytes.decode("ascii"))
        server.sendmail(
            sender_email, receiver_email, message.as_string())

# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []
