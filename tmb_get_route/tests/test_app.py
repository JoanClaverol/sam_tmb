import unittest
from app import get_journey_plan
from config import TMB_APP_ID, TMB_APP_KEY, HOME_LOCATION, WORK_LOCATION

class TestLambdaHandler(unittest.TestCase):
    def test_lambda_handler_success(self):
        # Call the handler
        result = get_journey_plan(HOME_LOCATION, WORK_LOCATION, TMB_APP_ID, TMB_APP_KEY)

        # Assertions
        self.assertIsInstance(result, dict)
        self.assertIn("requestParameters", result)
        self.assertTrue(result["requestParameters"])
        self.assertIn("plan", result)
        self.assertTrue(result["plan"])
        self.assertIn("metadata", result)

if __name__ == '__main__':
    unittest.main()