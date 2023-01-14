from typing import Any, Text, Dict, List
import requests
import json
import os
from datetime import datetime
from SPARQLWrapper import SPARQLWrapper, JSON, POST

#
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class ActionValues():

    @staticmethod
    def get_messagetext(tracker: Tracker):
        return {
            'text': tracker.latest_message['text']
        }


class ActionEvaluateBirthday(Action):

    sparql_url = "http://localhost:8080/sparql"
    qanary_pipeline = "http://localhost:8080"
    warning_no_birthdate_found = """<div class="no_result_found">I could not find any birthdate. If this is not expected, has their name been recognized correct? Try asking a different way. I also helps me if you use upper and lower case.</div>"""

    def __init__(self):
        try:
            hostip = os.getenv('QANARY_IP')
            if hostip is not None and hostip != "":
                self.sparql_url = "http://" + hostip + ":8080/sparql"
                self.qanary_pipeline = "http://" + hostip + ":8080"
        except Exception as e:
            pass
        print("use endpoints: {}, {} ".format(
            self.sparql_url, self.qanary_pipeline))

    def name(self) -> Text:
        return "action_evaluate_birthday"

    def start_sparql_request(self, payload):
        try:
            sparql = SPARQLWrapper(self.sparql_url)
            sparql.setQuery(payload)
            sparql.setReturnFormat(JSON)
            jsonobj = sparql.query().convert()
            result = jsonobj["results"]["bindings"]
            return result
        except Exception as e:
            return "I could not interact with Qanary triplestore at " + self.sparql_url + " due to the error " + type(e).__name__

    def get_result_from_binding(self, binding):
        result_text = binding["json"]["value"].replace("\\", "")
        result_json = json.loads(result_text)
        result = result_json["results"]["bindings"]
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
            return self.warning_no_birthdate_found
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

            table = table + "\n</table>"

            return prefix + table

    def retrieve_recognition_values_from_graph_and_build_answers(self, input, graph_id):
        payload = """
            PREFIX  qa:   <http://www.wdaqua.eu/qa#>
            PREFIX  oa:   <http://www.w3.org/ns/openannotation/core/>
            PREFIX  dbr:  <http://dbpedia.org/resource/>
            PREFIX  rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            SELECT ?resource ?start ?end
            WHERE  { 
                GRAPH <""" + graph_id + """> { 
                    ?annotation oa:hasBody ?resource ;
                                qa:score ?annotationScore ;
                                oa:hasTarget ?target .
                    ?target oa:hasSource ?source ;
                            oa:hasSelector  ?textSelector .
                    ?textSelector   rdf:type oa:TextPositionSelector ;
                                    oa:start ?start ;
                                    oa:end ?end .
                }
            }
            ORDER BY ?start 
            """
        bindings = self.start_sparql_request(payload)
        if isinstance(bindings, str):
            return bindings
        else:
            return self.build_recognition_table(input, bindings)

    def build_result_text_from_val(self, val, key):
        """
            Builds the text for the result from the value and the key if a label is available then it is embedded in the result
        """
        if key in val:
            if key + 'Label' in val and val[key + 'Label']['value'] != "":
                # return label with link
                return "<a href=\"{}\">{}</a>".format(val[key]['value'], val[key + 'Label']['value'])
            else:
                # return text only
                return val[key]['value']
        else:
            return ""

    def build_result_table(self, bindings):
        if len(bindings) == 0:
            return self.warning_no_birthdate_found
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
                if len(result) == 0:
                    return self.warning_no_birthdate_found

                for val in result:
                    row = """
                        <tr>
                            <td>{}</td>
                            <td>{}</td>
                            <td>{}</td>
                        </tr>
                        """.format(
                        self.build_result_text_from_val(val, 'person'),
                        self.build_result_text_from_val(val, 'birthplace'),
                        self.build_result_text_from_val(val, 'birthdate')
                    )
                    table = table + "\n" + row

            table = table + "\n</table>"

            return prefix + table

    def retrieve_birthdate_values_from_graph_and_build_answers(self, graph_id):
        payload = """
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX oa: <http://www.w3.org/ns/openannotation/core/>
            PREFIX qa: <http://www.wdaqua.eu/qa#>
            SELECT * 
            FROM <GRAPHID>
            WHERE {
                ?annotationId rdf:type qa:AnnotationOfAnswerJson.
                ?annotationId oa:hasBody ?body.
                ?body rdf:type qa:AnswerJson.
                ?body rdf:value ?json.
            }
            """.replace("<GRAPHID>", "<" + graph_id + ">")

        result = self.start_sparql_request(payload)

        if isinstance(result, str):
            return result

        table = self.build_result_table(result)

        answer = "" + table
        return answer

    def run_pipeline_query(self, text):
        try:
            pipeline_request_url = self.qanary_pipeline + "/questionanswering?textquestion=" + text + \
                "&language=en&componentlist%5B%5D=AutomationServiceComponent, BirthDataQueryBuilderWikidata, SparqlExecuterComponent"
            response = requests.request("POST", pipeline_request_url)
            response_json = json.loads(response.text)
            return response_json["inGraph"]
        except Exception as e:
            return "Could not interact with Qanary system at " + self.qanary_pipeline + " due to the error: " + type(e).__name__

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = tracker.latest_message['text']
        graph_id = self.run_pipeline_query(text)

        answer = self.retrieve_answer(text, graph_id)

        dispatcher.utter_message(text=answer)

        return []

    def retrieve_answer(self, text, graph_id):

        if 'urn' in graph_id:
            answer = self.retrieve_recognition_values_from_graph_and_build_answers(
                text, graph_id)
            answer = answer + "\n" + \
                self.retrieve_birthdate_values_from_graph_and_build_answers(
                    graph_id)
        else:
            answer = graph_id

        while("  " in answer):
            answer = answer.replace("  ", "")

        return answer
