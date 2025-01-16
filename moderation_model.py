import requests
from typing import List, Type
import os
import nltk
import joblib
from log import logger
from pymongo import MongoClient
import logging
import numpy as np
import time  # New for performance tracking

from model_updater import ModelUpdater
from filters import (
    BaseFilter,
    HomoPhobiaFilter,
    SuicideFilter,
    RacismFilter,
    TappouhkausFilter,
    FatPhobiaFilter,
    SexualHarassmentFilter,
    SexualViolenceFilter,
    PannaaksFilter,
    SwearingFilter,
    BoyFilter,
    InclusiveSafetyFilter,
    CustomFilter
)

from results import ModerationResult
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger("HaSpDe")
nltk.download('punkt')

LOG_SERVER_URL = "https://haspde.luova.club/log_comment"

# Priority levels for moderation results
MODERATION_PRIORITY = {
    ModerationResult.ACCEPT: 1,
    ModerationResult.HUMAN_REVIEW: 2,
    ModerationResult.HIDE: 3,
    ModerationResult.REMOVE: 4,
    ModerationResult.BAN: 5,
}

# Adding performance tracking decorator
def performance_tracker(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Function {func.__name__} executed in {duration:.4f} seconds")
        return result
    return wrapper

@performance_tracker
def get_most_probable_class_and_percent(model, X):
    """
    Retrieve the most probable class and its corresponding confidence percentage from the model.

    Parameters
    ----------
    model : sklearn.base.BaseEstimator
        The trained machine learning model used for prediction.
    X : array-like
        The input data for which predictions are to be made.

    Returns
    -------
    tuple
        A tuple containing:
        - most_probable_class_index (int): The index of the most probable class.
        - most_probable_percent (float): The confidence percentage of the prediction.
    """
    probabilities = model.predict_proba(X)
    most_probable_class_index = np.argmax(probabilities, axis=1)[0]  # First element
    most_probable_percent = probabilities[0, most_probable_class_index] * 100  # First row
    logger.info(f"Most probable class: {most_probable_class_index}, Confidence: {most_probable_percent:.2f}%")
    return most_probable_class_index, most_probable_percent

class ModerationModel:
    def __init__(self, learns=True, human_review=False, certainty_needed=80,
                 model_file="moderation_model.joblib", vectorizer_file="tfidf_vectorizer.joblib"):
        self.updater = ModelUpdater()
        self.model_file = model_file
        self.vectorizer_file = vectorizer_file
        self.model = self.load_model()
        self.vectorizer = self.load_vectorizer()  # Load vectorizer
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
            BoyFilter,
            InclusiveSafetyFilter
        ]
        self._initialize()

    @performance_tracker
    def load_model(self, attempt=0, max_attempts=2):
        """
        Load the machine learning model with retry logic.

        Parameters
        ----------
        attempt : int, optional
            The current attempt number (default is 0).
        max_attempts : int, optional
            The maximum number of retry attempts allowed (default is 2).

        Returns
        -------
        sklearn.base.BaseEstimator
            The loaded machine learning model.

        Raises
        ------
        SystemExit
            If the model fails to load after the maximum number of attempts.
        """
        # Check for model updates
        self.updater.update_model()

        try:
            # Attempt to load the model
            model = joblib.load(self.model_file)
            logger.info("🔥 Existing model loaded successfully. Let's go!")
        except Exception as e:
            logger.error(f"💔 Failed to load the model: {e}. Attempting to reinitialize it!")
            
            # Try to force reinitialize the model
            try:
                self.updater.update_model(force=True)
                logger.info("🎨 Model reinitialized successfully.")
            except Exception as reinit_error:
                logger.error(f"❌ Error during reinitialization: {reinit_error}. Exiting.")
                exit(1)

            # Retry the loading process if maximum attempts not reached
            if attempt < max_attempts:
                logger.info(f"🔁 Retrying model load (attempt {attempt + 1}/{max_attempts})...")
                return self.load_model(attempt=attempt + 1, max_attempts=max_attempts)
            else:
                logger.critical("💀 Maximum retries exceeded. Exiting.")
                exit(1)

        return model


    @performance_tracker
    def load_vectorizer(self, attempt=0, max_attempts=2):
        """
        Load the TF-IDF vectorizer with retry logic and error handling.

        Parameters
        ----------
        attempt : int, optional
            The current attempt number (default is 0).
        max_attempts : int, optional
            The maximum number of retry attempts allowed (default is 2).

        Returns
        -------
        sklearn.feature_extraction.text.TfidfVectorizer
            The loaded TF-IDF vectorizer.

        Raises
        ------
        SystemExit
            If the vectorizer fails to load after the maximum number of attempts.
        """
        try:
            # Attempt to load the vectorizer
            vectorizer = joblib.load(self.vectorizer_file)
            logger.info("🎨 Vectorizer loaded successfully.")
        except Exception as e:
            logger.error(f"🛑 Failed to load vectorizer: {e}. Attempting to reinitialize model...")

            # Try to force reinitialize the model
            try:
                self.updater.update_model(force=True)
                logger.info("🎨 Model reinitialized successfully.")
            except Exception as reinit_error:
                logger.error(f"❌ Error during reinitialization: {reinit_error}. Exiting.")
                exit(1)

            # Retry loading the vectorizer if maximum attempts not reached
            if attempt < max_attempts:
                logger.info(f"🔁 Retrying vectorizer load (attempt {attempt + 1}/{max_attempts})...")
                return self.load_vectorizer(attempt=attempt + 1, max_attempts=max_attempts)
            else:
                logger.critical("💀 Maximum retries exceeded. Exiting.")
                exit(1)

        return vectorizer


    def _initialize(self):
        self.filters = [filter() for filter in self.filters]  # Instantiate each filter and store it
        for filter in self.filters:
            logger.info(f"🚀 Initializing {filter.__class__.__name__}")

    def _01_label(self, label):
        return 0 if label in [0] else 1
    @performance_tracker
    def moderate_comment(self, comment, config={}, interactive=False):
        """
        Moderate a comment based on predefined filters and model predictions.

        Parameters
        ----------
        comment : str
            The comment to be moderated.
        config : dict, optional
            Configuration options for moderation, including custom filters (default is empty dict).
        interactive : bool, optional
            Flag to enable interactive mode for user feedback (default is False).

        Returns
        -------
        ModerationResult
            The final moderation result after applying filters and model predictions.
        """
        highest_result = ModerationResult.ACCEPT  # Start with the lowest moderation level
        
        filt = []

        if config != {} and not config is None:
            filters = config.get("filters", [])
            for filter in filters:
                filt.append(CustomFilter(filter.get("name"), filter.get("0_action", None), filter.get("1_action", None)))
        
        filt.extend(self.filters)

        # Run all filters
        for filter_instance in filt:
            result = filter_instance.apply(comment)
            logger.info(f"🔍 Filter {filter_instance.__class__.__name__} returned: {result}")

            if MODERATION_PRIORITY[int(result)] > MODERATION_PRIORITY[highest_result]:
                highest_result = int(result)

        transformed_comment = self.vectorizer.transform([comment])  # Transform the input comment

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
        input_data = self.vectorizer.transform([comment])
        most_probable_class, percent = get_most_probable_class_and_percent(self.model, input_data)    

        model_result = ModerationResult.HIDE if most_probable_class == 1 else ModerationResult.ACCEPT
        logger.info(f'🤖 Model moderation result: {model_result} with certainty {percent:.2f}%')

        # Check confidence level and adjust the result based on certainty
        if percent >= self.certainty_needed:
            if MODERATION_PRIORITY[model_result] > MODERATION_PRIORITY[highest_result]:
                highest_result = model_result

        highest_result = self.feedback(interactive, highest_result, percent, model_result)

        # If the result is still human review, and interactive mode is enabled
        if highest_result == ModerationResult.HUMAN_REVIEW:
            logger.warning("🤷‍♀️ Uncertain about comment, requesting human review.")
        
        # Log the final moderation result
        self._log_comment(self._01_label(highest_result), highest_result, comment)
        logger.info(f'🎉 Comment "{comment}" received final moderation result: {highest_result}')
        
        return highest_result

    def feedback(self, interactive, highest_result, percent, model_result):
        """
        Handle user feedback in interactive mode to adjust moderation results.

        Parameters
        ----------
        interactive : bool
            Indicates if interactive mode is enabled.
        highest_result : ModerationResult
            The current highest priority moderation result.
        percent : float
            The confidence percentage of the model's prediction.
        model_result : ModerationResult
            The initial moderation result from the model.

        Returns
        -------
        ModerationResult
            The updated moderation result based on user feedback.
        """
        if interactive:
            user_feedback = input(f"""🤖 Model moderation result: {model_result} with certainty {percent:.2f}%.\nWas this correct? (Y/N): """).strip().upper()
                
            if user_feedback == "Y":
                logger.info("👍 User confirmed model prediction.")
                model_result = ModerationResult.ACCEPT if model_result == ModerationResult.ACCEPT else ModerationResult.HIDE
                if model_result == ModerationResult.ACCEPT:
                    if highest_result != ModerationResult.ACCEPT:
                        highest_result = ModerationResult.ACCEPT


                elif model_result == ModerationResult.HIDE:
                    if highest_result not in [1, 2, 3]:
                        highest_result = 1

                else:
                    pass
                        

            elif user_feedback == "N":
                logger.info("🔄 User indicated incorrect prediction. Flipping result.")
                model_result = ModerationResult.ACCEPT if model_result == ModerationResult.HIDE else ModerationResult.HIDE
                highest_result = model_result
            else:
                logger.warning("Invalid input. Proceeding with the model result.")
        return highest_result


    @performance_tracker
    def _log_comment(self, label, action_type, comment):
        """
        Log the moderated comment with its associated label and action type.

        Parameters
        ----------
        label : int
            The numerical label representing the moderation decision.
        action_type : int
            The type of action to be taken based on the label.
        comment : str
            The content of the moderated comment.
        """
        if self.learns:
            api_url = "https://updates.haspde.luova.club/comments"
            action_mapping = {
                "ACCEPT": 0,
                "HIDE": 1,
                "REMOVE": 2,
                "BAN": 3,
                "HUMAN_REVIEW": 4
            }
            
            action_numeric = action_mapping.get(action_type, None) if type(action_type) != int else action_type

            if action_numeric is not None:
                payload = {
                    "label": label,
                    "action_type": action_numeric,
                    "comment": comment
                }
                
                try:
                    response = requests.post(api_url, json=payload)
                    response.raise_for_status()
                    logger.info(f"🌍 Comment '{comment}' logged with label {label} and action type {action_numeric}.")
                except requests.exceptions.RequestException as e:
                    logger.error(f"🌩️ Failed to log comment '{comment}': {e}")
            else:
                logger.error(f"Invalid action type: {action_type}")
        else:
            logger.debug("Learning disabled by config. Not adding to training data.")

    def ask_for_human_review(self, comment):
        """
        Prompt for human review of a comment when moderation confidence is low.

        Parameters
        ----------
        comment : str
            The comment requiring human review.

        Returns
        -------
        int
            User input indicating approval (0) or flagging (1) of the comment.
        """
        while True:
            try:
                transformed_comment = self.vectorizer.transform([comment])
                most_probable_class, percent = get_most_probable_class_and_percent(self.model, transformed_comment)
                print(f"\nModel prediction:\n- Class: {most_probable_class}\n- Probability: {percent:.2f}%\n")
                human_input = int(input(f"Review the comment: '{comment}'\nEnter 1 to flag or 0 to approve: "))
                if human_input in [0, 1]:
                    return human_input
                else:
                    logger.warning("🤔 Invalid input. Please enter 1 or 0.")
            except ValueError:
                logger.warning("🤔 Invalid input. Please enter 1 or 0.")


if __name__ == "__main__":
    model = ModerationModel()
    while True:
        Q = input("Q: ")
        if Q == "quit":
            break
        result = model.moderate_comment(Q, interactive=True)
        print("A:", result)
