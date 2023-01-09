from typing import Any, Text, Dict, List
import requests
import json
from datetime import datetime

#
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class ActionValues():

    @staticmethod
    def get_messagetext (tracker: Tracker):
        return {
            'text': tracker.latest_message['text']
        }

class ActionEvaluateBirthday(Action):
    
    sparql_url = "http://admin:admin@demos.swe.htwk-leipzig.de:40100/qanary/query"
    qanary_pipeline= "http://localhost:8080"

    def name(self) -> Text:
        return "action_evaluate_birthday"

    def start_sparql_request(self, payload):
        headers = {
        'Content-Type': 'application/sparql-query',
        'Accept': 'application/sparql-results+json'
        }

        try:
            response = requests.request("POST", self.sparql_url, headers=headers, data=payload)
            jsonobj = json.loads(response.text)
            result = jsonobj ["results"]["bindings"]     
            return result
        except Exception as e:
            return "I could not interact with Stardog due to the error " + type(e).__name__

    def get_result_from_binding(self, binding):
        result_text = binding["json"]["value"].replace("\\", "")
        result_json = json.loads(result_text)
        result = result_json ["results"]["bindings"]
        return result

    def get_recognition_table_row(self):
        return """
                <tr>
                    <td>FIRST_NAME</td>
                    <td>MIDDLE_NAME</td>
                    <td>LAST_NAME</td>
                </tr>
                """
    def finish_recognition_row(self, row):
        return row.replace("FIRST_NAME", "").replace("MIDDLE_NAME", "").replace("LAST_NAME", "")

    def build_recognition_table(self, input, bindings):
        if len(bindings) == 0:
            return "\n I did not recognize any person. If this is not expected, try asking a different way and use upper and lower case."
        else:
            prefix = "I have recognized the following entities (only First and Last Name are used for the birthdate):"
            table = """
                <table>
                    <tr>
                        <th>First Name</th>
                        <th>Middle Name</th>
                        <th>Last Name</th>
                    </tr>
                """
            row = self.get_recognition_table_row()
            if len(bindings) != 0:
                for binding in bindings:
                    resource = binding["resource"]["value"]
                    start = binding["start"]["value"]
                    end = binding["end"]["value"]

                    if resource in row:
                        row = row.replace(resource, input[int(start):int(end)])
                    else:
                        row = self.finish_recognition_row(row)
                        table = table + "\n" + row
                        row = self.get_recognition_table_row()
                row = self.finish_recognition_row(row)
                table = table + "\n" + row

            return prefix + table + "\n</table>"

    def retrieve_recognition_values_from_graph_and_build_answers(self, input, graph_id):
        payload = "PREFIX  qa:   <http://www.wdaqua.eu/qa#>\nPREFIX  oa:   <http://www.w3.org/ns/openannotation/core/>\nPREFIX  dbr:  <http://dbpedia.org/resource/>\nPREFIX  rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n\nSELECT ?resource ?start ?end\nWHERE\n  { GRAPH <" + graph_id + ">\n      { ?annotation  oa:hasBody   ?resource ;\n                  qa:score        ?annotationScore ;\n                  oa:hasTarget    ?target .\n        ?target   oa:hasSource    ?source ;\n                  oa:hasSelector  ?textSelector .\n        ?textSelector\n                  rdf:type        oa:TextPositionSelector ;\n                  oa:start        ?start ;\n                  oa:end          ?end\n      }\n  }\nORDER BY ?start"
        bindings = self.start_sparql_request(payload)
        if isinstance(bindings, str):
            return bindings
        else:
            return self.build_recognition_table(input, bindings)

    def build_result_table(self, bindings):
        if len(bindings) == 0:
            return "\n I could not find any birthdate. If this is not expected, has their name been recognized correct? Try asking a different way and use upper and lower case."
        else:
            table = """
                <table>
                    <tr>
                        <th>Person</th>
                        <th>Birthplace</th>
                        <th>Birthdate</th>
                    </tr>
                """
            
            prefix = "I have found the following persons and birthdates: \n"

            for binding in bindings:
                result = self.get_result_from_binding(binding)

                for val in result:
                        row = """
                        <tr>
                            <td>PERSON</td>
                            <td>BIRTHPLACE</td>
                            <td>BIRTHDATE</td>
                        </tr>
                        """
                        row = row.replace("PERSON", val['person']['value'])
                        row = row.replace("BIRTHPLACE", val['birthplace']['value'])
                        date = val['birthdate']['value']
                        datetime_object = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ').date()
                        row = row.replace("BIRTHDATE", f"{datetime_object}")
                        table = table + "\n" + row
                
            return prefix + table + "\n</table>"

    def retrieve_birthdate_values_from_graph_and_build_answers(self, graph_id):
        payload = "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\nPREFIX oa: <http://www.w3.org/ns/openannotation/core/>\nPREFIX qa: <http://www.wdaqua.eu/qa#>\nSELECT * \nFROM <GRAPHID>\nWHERE {\n    ?annotationId rdf:type qa:AnnotationOfAnswerJson.\n    ?annotationId oa:hasBody ?body.\n  \t?body rdf:type qa:AnswerJson.\n    ?body rdf:value ?json.\n}\n".replace("GRAPHID", graph_id)

        result = self.start_sparql_request(payload)

        if isinstance(result, str):
            return result  

        table = self.build_result_table(result)

        answer = "" + table
        return answer

    def run_pipeline_query(self, text):
        try:
            pipeline_request_url = self.qanary_pipeline + "/questionanswering?textquestion=" + text + "&language=en&componentlist%5B%5D=AutomationServiceComponent, BirthDataQueryBuilder, SparqlExecuterComponent"
            response = requests.request("POST", pipeline_request_url)
            response_json = json.loads(response.text)
            return response_json["inGraph"]
        except Exception as e:
            return "Could not interact with Qanary due to the error: " + type(e).__name__

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        
        text = tracker.latest_message['text']
        graph_id = self.run_pipeline_query(text)

        if 'urn' in graph_id:
            answer = self.retrieve_recognition_values_from_graph_and_build_answers(text, graph_id)
            answer = answer + "\n" + self.retrieve_birthdate_values_from_graph_and_build_answers(graph_id)
        else: 
            answer = graph_id

        while("  " in answer):
            answer = answer.replace("  ", "")
        
        dispatcher.utter_message(text=answer)

        return []