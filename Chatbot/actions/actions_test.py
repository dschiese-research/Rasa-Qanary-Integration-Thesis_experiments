import unittest
import logging
from actions import *

log_filename = 'actions_test.log'
logging.basicConfig(format='%(levelname)s - %(message)s')
logging.getLogger().setLevel(logging.INFO)


class TestRasaAction(unittest.TestCase):
    def test_connection_to_pipeline(self):
        graphid = self.fetch_graph_from_qanary(
            "When was Albert Einstein born?")
        assert graphid.startswith("urn:graph")

    def fetch_graph_from_qanary(self, text):
        action = ActionEvaluateBirthday()
        graphid = action.run_pipeline_query(text)
        logging.info(graphid)
        return graphid

    def test_retrieve_answer(self):
        action = ActionEvaluateBirthday()
        text = "When was Albert Einstein born?"
        graphid = self.fetch_graph_from_qanary(text)
        result = action.retrieve_answer(text, graphid)
        logging.info(result)
        assert "<table>" in result
        assert "<td>Albert</td>" in result
        assert "<td>Einstein</td>" in result
        assert "Q3012" in result
