import nltk
import requests
import joblib
from log import logger
from profane_detector import ProfaneDetector
from pymongo import MongoClient
from config import Config
from updater import ModelUpdater

nltk.download('punkt')
config = Config()

MODEL_FILE = 'moderation_model.joblib'
MODEL_VERSION_FILE = 'model_version.txt'
GITHUB_MODEL_URL = "https://raw.githubusercontent.com/botsarefuture/HaSpDe/main/moderation_model.joblib"
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/botsarefuture/HaSpDe/main/model_version.txt"
LOG_SERVER_URL = "https://haspde.luova.club/log_comment"  # Replace with your server URL

# MongoDB setup
client = MongoClient(config.MONGODB_URI)
db = client[config.DB_NAME]
comments_collection = db['comments']


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
    def __init__(self, learns=True, human_review=False, strict_anti_profane=False, certainty_needed=80):
        self.model = self.load_model()
        self.learns = learns
        self.human_review = human_review
        self.profane_detector = ProfaneDetector()
        self.strict_anti_profane = strict_anti_profane
        self.certainty_needed = certainty_needed

    def load_or_train_model(self):
        raise DeprecationWarning("This function is depraced, use load_model() instead.")
    
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
        # First, check if the comment is flagged by the profane detector
        if self.strict_anti_profane:
            is_profane = self.profane_detector.detect_api(None, comment)

        # Ask for feedback before taking action
        if self.human_review:
            feedback = self.ask_for_human_review(comment)
            if feedback in [0, 1]:
                self._log_comment(feedback, comment)
                
                if feedback == 0:
                    logger.info(f'Comment "{comment}" approved based on human review.')
                    return False

                if feedback == 1:
                    logger.info(f'Comment "{comment}" flagged for moderation based on human review.')
                    return True
                
            else:
                logger.warning("Invalid human review input. Defaulting to model prediction.")
                if self.strict_anti_profane:
                    return is_profane

        # If human review is disabled, proceed with automated moderation
        if self.strict_anti_profane and is_profane:
            self._log_comment(1, comment)
            logger.info(f'Comment "{comment}" flagged for moderation due to profanity.')
            return True

        # Use the trained model to get the most probable class and its probability
        most_probable_class, percent = get_most_probable_class_and_percent(self.model, [comment])

        # Log and return based on model prediction
        
        # We're not doing some random stuff
        if percent >= self.certainty_needed:
            if most_probable_class == 1:
                self._log_comment(1, comment)
                logger.info("Comment flagged for moderation.")
                return True
            elif most_probable_class == 0:
                self._log_comment(0, comment)
                logger.info("Comment approved.")
                return False
        else:
            logger.warning("Model uncertainty. Sending in for human review.")
            self._human_review_db(most_probable_class, percent, comment)
            return False

    def _human_review_db(self, most_probable_class, percent, comment):
        comment_real = comments_collection.find_one({'status': 'pending', 'comment': comment})

        if comment_real:
            comment_id = comment_real["id"]
            comment_text = comment
            
        
        comments_collection.insert_one({
                    'id': comment_id,
                    'text': comment_text,
                    'status': 'pending',
                    'evaluation': "positive" if most_probable_class == 0 else 'negative',
                    'platform': 'HaSpDe'
                })
        
    def _log_local(self, label, comment):
        # Log to local file
        filename = f"../training/{label}_future.txt"
        with open(filename, "a", encoding="utf-8") as f:
            f.write(comment + '\n')
            
    def _log_comment(self, label, comment):
        if self.learns:            
            
            """# Send to central server
            self._send_log_to_server(label, comment)""" # This will be used starting from V2
            
            self._log_local(label, comment)
            
            logger.debug(f"Added to future training data for label {label}.")
        else:
            logger.debug("Learning has been disabled by config. Won't add comments to future training data.")

    def _send_log_to_server(self, label, comment):
        data = {
            'label': label,
            'comment': comment,
            'platform': 'HaSpDe'
        }
        try:
            response = requests.post(LOG_SERVER_URL, json=data)
            if response.status_code == 201:
                logger.info("Log successfully sent to the central server.")
            else:
                logger.error(f"Failed to send log to the server. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending log to the server: {e}")
        
    def ask_for_human_review(self, comment):
        while True:
            try:
                # Use the trained model to get the most probable class and its probability
                most_probable_class, percent = get_most_probable_class_and_percent(self.model, [comment])

                # Show model results to the human reviewer
                print(f"\nModel prediction:\n- Class: {most_probable_class}\n- Probability: {percent}%\n")

                # Ask human for input
                human_input = int(input(f"Review the comment: '{comment}'\nEnter 1 to flag or 0 to approve: "))
                if human_input in [0, 1]:
                    return human_input
                else:
                    logger.warning("Invalid input. Please enter 1 or 0.")
            except ValueError:
                logger.warning("Invalid input. Please enter 1 or 0.")

if __name__ == "__main__":
    # Example usage from the command prompt
    model_instance = ModerationModel(learns=True, human_review=True)  # Set learns to True if you want to collect future training data
    while True:
        comment_to_moderate = input("Enter the comment to moderate (type 'exit' to quit): ")
        if comment_to_moderate.lower() == 'exit':
            break
        model_instance.moderate_comment(comment_to_moderate)
