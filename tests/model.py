import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import joblib
from moderation_model import ModerationModel  # Adjust the import as necessary
from results import ModerationResult

class TestModerationModel(unittest.TestCase):

    @patch('joblib.load')
    @patch('model_updater.ModelUpdater')
    def setUp(self, mock_model_updater, mock_joblib_load):
        # Setup mock model and vectorizer
        self.mock_model = MagicMock()
        self.mock_vectorizer = MagicMock()
        self.mock_model.predict_proba.return_value = np.array([[0.2, 0.8]])  # Simulate predictions
        mock_joblib_load.side_effect = [self.mock_model, self.mock_vectorizer]

        # Create an instance of the ModerationModel
        self.model = ModerationModel(learns=True)

    @patch('joblib.load')
    def test_load_model_success(self, mock_joblib_load):
        model = self.model.load_model()
        self.assertEqual(model, self.mock_model)
        mock_joblib_load.assert_called_once_with("moderation_model.joblib")

    @patch('joblib.load', side_effect=Exception("Load Error"))
    @patch('model_updater.ModelUpdater.update_model')
    def test_load_model_retry_success(self, mock_update_model, mock_joblib_load):
        mock_update_model.return_value = None  # Simulate successful update
        model = self.model.load_model()
        self.assertEqual(model, self.mock_model)
        self.assertEqual(mock_joblib_load.call_count, 2)  # Check that load was retried once

    @patch('joblib.load', side_effect=Exception("Load Error"))
    @patch('model_updater.ModelUpdater.update_model')
    def test_load_model_failure_exceeds_retries(self, mock_update_model, mock_joblib_load):
        mock_update_model.return_value = None  # Simulate successful update
        with self.assertRaises(SystemExit):  # Expecting exit on failure
            self.model.load_model(max_attempts=1)

    @patch('joblib.load')
    def test_load_vectorizer_success(self, mock_joblib_load):
        vectorizer = self.model.load_vectorizer()
        self.assertEqual(vectorizer, self.mock_vectorizer)
        mock_joblib_load.assert_called_once_with("tfidf_vectorizer.joblib")

    @patch('joblib.load', side_effect=Exception("Load Error"))
    @patch('model_updater.ModelUpdater.update_model')
    def test_load_vectorizer_retry_success(self, mock_update_model, mock_joblib_load):
        mock_update_model.return_value = None  # Simulate successful update
        vectorizer = self.model.load_vectorizer()
        self.assertEqual(vectorizer, self.mock_vectorizer)
        self.assertEqual(mock_joblib_load.call_count, 2)  # Check that load was retried once

    @patch('joblib.load', side_effect=Exception("Load Error"))
    @patch('model_updater.ModelUpdater.update_model')
    def test_load_vectorizer_failure_exceeds_retries(self, mock_update_model, mock_joblib_load):
        mock_update_model.return_value = None  # Simulate successful update
        with self.assertRaises(SystemExit):  # Expecting exit on failure
            self.model.load_vectorizer(max_attempts=1)

    @patch('nltk.download')
    @patch('moderation_model.get_most_probable_class_and_percent')
    @patch('moderation_model.ModerationModel.ask_for_human_review', return_value=0)  # Simulate human review
    def test_moderate_comment_accept(self, mock_human_review, mock_get_prob_class):
        mock_get_prob_class.return_value = (0, 85.0)  # Class 0 with 85% confidence
        result = self.model.moderate_comment("This is a safe comment.")
        self.assertEqual(result, ModerationResult.ACCEPT)

    @patch('nltk.download')
    @patch('moderation_model.get_most_probable_class_and_percent')
    @patch('moderation_model.ModerationModel.ask_for_human_review', return_value=0)  # Simulate human review
    def test_moderate_comment_hide(self, mock_human_review, mock_get_prob_class):
        mock_get_prob_class.return_value = (1, 75.0)  # Class 1 with 75% confidence
        result = self.model.moderate_comment("This comment is inappropriate.")
        self.assertEqual(result, ModerationResult.HIDE)

    @patch('nltk.download')
    @patch('moderation_model.get_most_probable_class_and_percent')
    @patch('moderation_model.ModerationModel.ask_for_human_review', return_value=1)  # Simulate human review
    def test_moderate_comment_human_review(self, mock_human_review, mock_get_prob_class):
        mock_get_prob_class.return_value = (1, 60.0)  # Class 1 with 60% confidence
        result = self.model.moderate_comment("This comment might need review.")
        self.assertEqual(result, ModerationResult.HUMAN_REVIEW)

if __name__ == "__main__":
    unittest.main()
