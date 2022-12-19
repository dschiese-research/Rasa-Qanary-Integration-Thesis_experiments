from typing import Any, Text, Dict, List
import requests
import json
import logging
#
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class ActionValues():
    URL='http://20.79.206.115:8002'

    @staticmethod
    def get_messagetext (tracker: Tracker):
        return {
            'text': tracker.latest_message['text']
        }

class ActionEvaluateBirthday(Action):

    def name(self) -> Text:
        return "action_evaluate_birthday"

    def build_result_table(self, reply):
        table = """
            <table>
                <tr>
                    <th>First Name</th>
                    <th>Second Name</th>
                    <th>Last Name</th>
                    <th>Birthdate</th>
                </tr>
            """
        extra = ""

        for result in reply:
            print(result)
            row = """
                <tr>
                    <td>FIRSTNAME</td>
                    <td>SECONDNAME</td>
                    <td>LASTNAME</td>
                    <td>BIRTHDATE</td>
                </tr>
            """
            row = row.replace("FIRSTNAME", result['FIRST_NAME'])
            row = row.replace("SECONDNAME", result['MIDDLE_NAME'])
            row = row.replace("LASTNAME", result['LAST_NAME'])
            row = row.replace("BIRTHDATE", result['birthdate'])
            table = table + "\n" + row
            if result['birthdate'] == "":
                extra = "\n I could not find a birtdate for all found people. If this is not expected, is their name correct?"

        return table + "\n</table>" + extra

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        #r = requests.get(ActionValues.URL + '/api?text=' + tracker.latest_message['text'])
        #reply = r.json()
        reply = {    
            "text": "When is the birthday of Barack Obama and Angela",
            "result": [
                {
                    "FIRST_NAME": "Barack",
                    "LAST_NAME": "Obama",
                    "MIDDLE_NAME": "",
                    "birthdate": "11.11.1111"
                },
                {
                    "FIRST_NAME": "Angela",
                    "LAST_NAME": "",
                    "MIDDLE_NAME": "",
                    "birthdate": ""
                }
            ]
        }
        
        answer = ""

        if len(reply["result"]) > 0 and (reply["result"][0]['FIRST_NAME'] != '' or reply["result"][0]['MIDDLE_NAME'] != '' or reply["result"][0]['LAST_NAME'] != ''):
            answer = "I have received the following result:\n" + self.build_result_table(reply["result"])
        else:
            answer = "I apologize; I could not recognize any name. Please ask me questions such as 'When was <Person> born?'. It helps me if you consider upper and lower case!"

        dispatcher.utter_message(text=answer)

        return []