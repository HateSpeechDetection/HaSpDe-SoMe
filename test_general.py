import unittest
from unittest.mock import patch, MagicMock
from moderation_model import ModerationModel, get_most_probable_class_and_percent
from results import ModerationResult
from filters import HomoPhobiaFilter, RacismFilter

class TestModerationModel(unittest.TestCase):

    @patch('moderation_model.ModelUpdater')  # Mock the ModelUpdater
    @patch('moderation_model.joblib.load')  # Mock the model loading
    @patch('moderation_model.requests.post')  # Mock requests for logging comments
    def setUp(self, mock_post, mock_load, mock_model_updater):
        # Mock model with predict_proba returning a test value
        self.mock_model = MagicMock()
        self.mock_model.predict_proba.return_value = [[0.9, 0.1]]  # Simulate a 90% confidence for class 0
        mock_load.return_value = self.mock_model
        
        # Mock for requests.post
        self.mock_post = mock_post
        
        # Instantiate the model under test
        self.model = ModerationModel()

    def test_moderate_comment(self):
        # Mocking the filters to return ModerationResult.ACCEPT
        for filter_instance in self.model.filters:
            filter_instance.apply = MagicMock(return_value=ModerationResult.ACCEPT)

        # Mock the API call for logging
        self.mock_post.return_value.status_code = 200

        # Test a comment
        result = self.model.moderate_comment("This is a test comment")
        
        # Assert that the comment was accepted
        self.assertEqual(result, ModerationResult.ACCEPT)

    def test_moderate_comment_hide(self):
        # Mocking the filters to return a higher priority result (HIDE)
        for filter_instance in self.model.filters:
            if isinstance(filter_instance, HomoPhobiaFilter):
                filter_instance.apply = MagicMock(return_value=ModerationResult.HIDE)
            else:
                filter_instance.apply = MagicMock(return_value=ModerationResult.ACCEPT)

        # Test a comment with homophobic content
        result = self.model.moderate_comment("This is a test comment with homophobia")

        # Assert that the comment is flagged for hiding
        self.assertEqual(result, ModerationResult.HIDE)

    def test_moderate_comment_model_prediction(self):
        # Simulate model predicting class 1 (should result in HIDE)
        self.mock_model.predict_proba.return_value = [[0.1, 0.9]]  # 90% confidence for class 1

        # Test a comment
        result = self.model.moderate_comment("This is a borderline comment")

        # Assert the result is HIDE due to model prediction
        self.assertEqual(result, ModerationResult.HIDE)

    def test_logging_comment(self):
        # Test logging by calling the moderate_comment function
        self.model._log_comment(1, "HIDE", "This is a logged comment")

        # Assert that the API request was made with the correct data
        self.mock_post.assert_called_once_with("https://updates.haspde.luova.club/comments", 
            json={"label": 1, "action_type": 1, "comment": "This is a logged comment"})

    def test_model_prediction_function(self):
        # Test the helper function get_most_probable_class_and_percent
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = [[0.1, 0.9]]  # 90% confidence for class 1

        most_probable_class, percent = get_most_probable_class_and_percent(mock_model, ["test"])

        # Assert that it returns the correct class and percent
        self.assertEqual(most_probable_class, 1)
        self.assertEqual(percent, 90.0)


if __name__ == "__main__":
    unittest.main()
