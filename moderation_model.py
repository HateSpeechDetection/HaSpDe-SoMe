import os
import nltk
import joblib
from log import logger
from profane_detector import ProfaneDetector
from pymongo import MongoClient
import os
import joblib
import logging
from updater import ModelUpdater

logger = logging.getLogger("HaSpDe")

nltk.download('punkt')

MODEL_FILE = 'moderation_model.joblib'
MODEL_VERSION_FILE = 'model_version.txt'
GITHUB_MODEL_URL = "https://raw.githubusercontent.com/botsarefuture/HaSpDe/main/moderation_model.joblib"
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/botsarefuture/HaSpDe/main/model_version.txt"
LOG_SERVER_URL = "https://S1.haspde.com/log_comment"

def get_most_probable_class_and_percent(model, X):
    # Get class probabilities using predict_proba
    probabilities = model.predict_proba(X)

    # Find the index of the class with the highest probability
    most_probable_class_index = probabilities.argmax(axis=1)

    # Get the corresponding probability for the most probable class
    most_probable_percent = probabilities[range(len(probabilities)), most_probable_class_index]

    # Return the most probable class and its probability
    return most_probable_class_index, most_probable_percent * 100

class ModerationResult:
    # Define constants for moderation actions
    ACCEPT = 0
    HIDE = 1
    REMOVE = 2
    BAN = 3
    HUMAN_REVIEW = 4
    
    # Map result codes to readable actions
    RESULT_MAPPING = {
        ACCEPT: "ACCEPT",
        HIDE: "HIDE",
        REMOVE: "REMOVE",
        BAN: "BAN",
        HUMAN_REVIEW: "HUMAN_REVIEW"
    }

    def __init__(self, result: str | int | bool | None = None, is_error: bool | None = False) -> 'ModerationResult':
        self.result = result
        self.is_error = is_error

    def __repr__(self) -> str:
        return f"<ModerationResult(result={self.result}, is_error={self.is_error})>"

    def __str__(self) -> str:
        return f"{self.RESULT_MAPPING.get(self.result, 'UNKNOWN')}"

    def __int__(self) -> int:
        return int(self.result) if isinstance(self.result, int) else -1

    def __call__(self, *args: any, **kwds: any) -> any:
        return self.RESULT_MAPPING.get(self.result, 'UNKNOWN')

    def __bool__(self) -> bool:
        # The result is considered False if there's an error or the result is None
        return not self.is_error and self.result is not None

class ModerationModel:
    def __init__(self, learns=True, human_review=False, certainty_needed=80):
        self.model = self.load_model()
        self.learns = learns
        self.human_review = human_review
        self.certainty_needed = certainty_needed

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

    def moderate_comment(self, comment):
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
            self._log_comment(most_probable_class, comment)
            action = "flagged for moderation" if most_probable_class == 1 else "approved"
            logger.info(f'Comment "{comment}" {action}.')
            return ModerationResult(ModerationResult.HIDE if most_probable_class == 1 else ModerationResult.ACCEPT)
        
        else:
            logger.warning("Uncertain about comment, requesting human review.")
            return ModerationResult(ModerationResult.HUMAN_REVIEW)

    def _log_comment(self, label, comment):
        if self.learns:
            filename = f"../training/{label}_future.txt"
            with open(filename, "a", encoding="utf-8") as f:
                f.write(comment + '\n')
            logger.debug(f"Added to future training data for label {label}.")
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