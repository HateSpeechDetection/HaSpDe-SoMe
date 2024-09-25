import requests
from typing import List, Type
import os
import nltk
import joblib
from log import logger
#from profane_detector import ProfaneDetector
from pymongo import MongoClient
import os
import joblib
import logging
from updater import ModelUpdater
from results import ModerationResult
from filters import BaseFilter, HomoPhobiaFilter, SuicideFilter, RacismFilter, TappouhkausFilter, FatPhobiaFilter, SexualHarassmentFilter, SexualViolenceFilter, PannaaksFilter, SwearingFilter, BoyFilter

logger = logging.getLogger("HaSpDe")

nltk.download('punkt')

MODEL_FILE = 'HaSpDe/HaSpDe'
MODEL_VERSION_FILE = './model_version.txt'
GITHUB_MODEL_URL = "https://raw.githubusercontent.com/botsarefuture/HaSpDe/main/moderation_model.joblib"
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/botsarefuture/HaSpDe/main/model_version.txt"
LOG_SERVER_URL = "https://haspde.luova.club/log_comment"

# Priority levels for moderation results
MODERATION_PRIORITY = {
    ModerationResult.ACCEPT: 1,
    ModerationResult.HUMAN_REVIEW: 2,
    ModerationResult.HIDE: 3,
    ModerationResult.REMOVE: 4,
    ModerationResult.BAN: 5,
}


def get_most_probable_class_and_percent(model, X):
    # Get class probabilities using predict_proba
    probabilities = model.predict_proba(X)

    # Find the index of the class with the highest probability
    most_probable_class_index = probabilities.argmax(axis=1)

    # Get the corresponding probability for the most probable class
    most_probable_percent = probabilities[range(len(probabilities)), most_probable_class_index]

    # Return the most probable class and its probability
    return most_probable_class_index, most_probable_percent * 100

class ModerationModel:
    def __init__(self, learns=True, human_review=False, certainty_needed=80):
        self.model = self.load_model()
        self.learns = learns
        self.human_review = human_review
        self.certainty_needed = certainty_needed
        self.filters: List[Type[BaseFilter]] = [
                HomoPhobiaFilter,
                RacismFilter,
                SuicideFilter,
                SwearingFilter,
                TappouhkausFilter,
                FatPhobiaFilter,
                SexualViolenceFilter,
                SexualHarassmentFilter,
                PannaaksFilter,
                BoyFilter
        ]

        self._initialize()



    def load_model(self):
        updater = ModelUpdater(
            model_file=MODEL_FILE,
            version_file=MODEL_VERSION_FILE,
            model_url=GITHUB_MODEL_URL,
            version_url=GITHUB_VERSION_URL
        )
        
        updater.update_model()

        try:
            model = joblib.load(MODEL_FILE)
            logger.debug("Existing model loaded.")
        except Exception as e:
            logger.error(f"Failed to load the model: {e}")
            exit()

        return model
    
    def _initialize(self):
        self.filters = [filter() for filter in self.filters]  # Instantiate each filter and store it
        for filter in self.filters:
            logger.info(f"Initializing {filter.__class__.__name__}")
            filter.update_word_list()


    def _01_label(self, label):
        return 0 if label in [0] else 1

    def moderate_comment(self, comment):
        highest_result = ModerationResult.ACCEPT  # Start with the lowest moderation level
        allowed_action = [1, 2, ]
        
        # Run all filters
        for filter_instance in self.filters:
            result = filter_instance.apply(comment)
            logger.info(f"Filter {filter_instance.__class__.__name__} returned: {result}")

            # Compare result with the current highest result and update if necessary
            if MODERATION_PRIORITY[int(result)] > MODERATION_PRIORITY[highest_result]:
                highest_result = int(result)

        # Human review option
        if self.human_review:
            feedback = self.ask_for_human_review(comment)
            if feedback in [0, 1]:
                self._log_comment(feedback, comment)
                action = "approved" if feedback == 0 else "flagged for moderation"
                logger.info(f'Comment "{comment}" {action} based on human review.')
                return ModerationResult(ModerationResult.ACCEPT if feedback == 0 else ModerationResult.HIDE)
            
            else:
                logger.warning("Invalid human review input. Please try again.")
                return self.moderate_comment(comment)

        # Model prediction
        most_probable_class, percent = get_most_probable_class_and_percent(self.model, [comment])
        if percent >= self.certainty_needed:
            model_result = ModerationResult.HIDE if most_probable_class == 1 else ModerationResult.ACCEPT
            logger.info(f'Model moderation result: {model_result} with certainty {percent}%')
            
            # Compare the model result with the current highest result
            if MODERATION_PRIORITY[model_result] > MODERATION_PRIORITY[highest_result]:
                highest_result = model_result
        
        if highest_result == ModerationResult.HUMAN_REVIEW:
            logger.warning("Uncertain about comment, requesting human review.")
        
        # Log and return the highest moderation result
        self._log_comment(self._01_label(highest_result), highest_result, comment)
        logger.info(f'Comment "{comment}" received final moderation result: {highest_result}')
        return highest_result

    def _log_comment(self, label, action_type, comment):
        """
        This function should save to future training data via API.

        Args:
            label (int): Numeric label indicating positive (0) or negative (1).
            action_type (str): Action label indicating the comment's moderation status.
            comment (str): The comment to log.
        """
        if self.learns:
            api_url = "https://updates.haspde.luova.club/comments"  # Replace with your actual API URL
            
            # Map action types to their corresponding numeric values
            action_mapping = {
                "ACCEPT": 0,
                "HIDE": 1,
                "REMOVE": 2,
                "BAN": 3,
                "HUMAN_REVIEW": 4
            }
            
            # Determine the numeric action based on the action_type
            action_numeric = action_mapping.get(action_type, None) if type(action_type) != int else action_type

            if action_numeric is not None:
                payload = {
                    "label": label,  # Use the provided label (0 or 1)
                    "action_type": action_numeric,  # Numeric value of the action
                    "comment": comment
                }
                
                try:
                    response = requests.post(api_url, json=payload)
                    response.raise_for_status()  # Raise an error for bad responses
                    logger.debug(f"Comment '{comment}' logged with label {label} and action type {action_numeric}.")
                except requests.exceptions.RequestException as e:
                    logger.error(f"Failed to log comment '{comment}': {e}")
            else:
                logger.error(f"Invalid action type: {action_type}")
        else:
            logger.debug("Learning disabled by config. Not adding to training data.")

    def ask_for_human_review(self, comment):
        while True:
            try:
                most_probable_class, percent = get_most_probable_class_and_percent(self.model, [comment])
                print(f"\nModel prediction:\n- Class: {most_probable_class}\n- Probability: {percent}%\n")
                human_input = int(input(f"Review the comment: '{comment}'\nEnter 1 to flag or 0 to approve: "))
                if human_input in [0, 1]:
                    return human_input
                else:
                    logger.warning("Invalid input. Please enter 1 or 0.")
            except ValueError:
                logger.warning("Invalid input. Please enter 1 or 0.")


if __name__ == "__main__":
    model = ModerationModel()
    while True:
        Q = input("Q: ")
        if Q == "quit":
            break
        result = model.moderate_comment(Q)
        print("A:", result)


