from results import ModerationResult
import requests
import logging
import json
import os

# Set up logging
logger = logging.getLogger("HaSpDe")

class BaseFilter:
    """
    Base class for all text filters.

    Attributes:
        BASE_UPDATE_URL (str): The base URL where word lists are hosted for all filters.
        offensive_words (list): A list of words considered offensive for the specific filter type.
        filter_type (str): Type of the filter (e.g., "homophobia", "racism").
        local_version (str): Local version of the word list, used to check for updates.
        update_url (str): URL to fetch the word list for the specific filter.
        version_url (str): URL to fetch the version of the word list for the specific filter.
    """
    
    BASE_UPDATE_URL = "https://updates.haspde.luova.club/filters"  # Base update URL for all filters

    def __init__(self, filter_type: str):
        self.offensive_words = []
        self.filter_type = filter_type
        self.local_version = "0"  # Local version of the word list
        self.update_url = f"{self.BASE_UPDATE_URL}/{filter_type}"
        self.version_url = f"{self.update_url}/version"
        self.update_word_list()

    def update_word_list(self):
        """
        Fetches the updated word list from the server if a newer version is available.
        """
        try:
            response = requests.get(self.version_url)
            response.raise_for_status()
            server_version = response.text.strip()

            if server_version != self.local_version:
                logger.info(f"Updating {self.filter_type} word list from {self.update_url}...")
                word_list_response = requests.get(self.update_url)
                word_list_response.raise_for_status()
                
                # Save the new word list locally
                self.offensive_words = word_list_response.json().get('words', [])
                self.save_word_list()  # Save to local file
                self.local_version = server_version
                logger.info(f"Updated {self.filter_type} word list: {self.offensive_words[:10]}...")  # Log first 10 words for brevity
            else:
                logger.info(f"{self.filter_type.capitalize()} word list is up to date.")
                
        except Exception as e:
            logger.error(f"Failed to update {self.filter_type} word list: {e}")

    def save_word_list(self):
        """
        Saves the offensive words list to a local file.
        """
        os.makedirs(f"filters", exist_ok=True)
        with open(f"filters/{self.filter_type}_words.json", "w") as f:
            json.dump({"words": self.offensive_words}, f)
        logger.info(f"Saved {self.filter_type} word list to {self.filter_type}_words.json")

    def apply(self, text) -> ModerationResult:
        """
        Applies the filter logic to the input text.

        Returns:
            ModerationResult: Result of the moderation, indicating the action to be taken (e.g., BAN, ACCEPT).

        Raises:
            NotImplementedError: This method must be implemented in subclasses.
        """
        raise NotImplementedError("Subclasses should implement this method.")



# Subclasses using the BaseFilter with filter_type defined:

class HomoPhobiaFilter(BaseFilter):
    """
    Filter for detecting homophobic language in text.
    """
    def __init__(self):
        """
        Initializes the HomoPhobiaFilter with the input text.

        Args:
            text (str): The text to be filtered.
        """
        super().__init__(filter_type="homophobia")

    def apply(self, text) -> ModerationResult:
        """
        Applies the homophobia filter to the text.

        Returns:
            ModerationResult: BAN if offensive words are detected, otherwise ACCEPT.
        """
        if any(word in text.lower() for word in self.offensive_words):
            logger.info(f"Hate speech detected in comment: '{text}'")
            return ModerationResult(ModerationResult.HUMAN_REVIEW)
        return ModerationResult(ModerationResult.ACCEPT)


class RacismFilter(BaseFilter):
    """
    Filter for detecting racist language in text.
    """
    def __init__(self):
        """
        Initializes the RacismFilter with the input text.

        Args:
            text (str): The text to be filtered.
        """
        super().__init__(filter_type="racism")

    def apply(self, text) -> ModerationResult:
        """
        Applies the racism filter to the text.

        Returns:
            ModerationResult: BAN if offensive words are detected, otherwise ACCEPT.
        """
        if any(word in text.lower() for word in self.offensive_words):
            logger.info(f"Racist content detected in comment: '{text}'")
            return ModerationResult(ModerationResult.BAN)
        return ModerationResult(ModerationResult.ACCEPT)


class SuicideFilter(BaseFilter):
    """
    Filter for detecting suicidal content in text.
    """
    def __init__(self):
        """
        Initializes the SuicideFilter with the input text.

        Args:
            text (str): The text to be filtered.
        """
        super().__init__(filter_type="suicide")

    def apply(self, text) -> ModerationResult:
        """
        Applies the suicide filter to the text.

        Returns:
            ModerationResult: HUMAN_REVIEW if concerning content is detected, otherwise ACCEPT.
        """
        if any(word in text.lower() for word in self.offensive_words):
            logger.info(f"Suicidal content detected in comment: '{text}'")
            return ModerationResult(ModerationResult.HUMAN_REVIEW)
        return ModerationResult(ModerationResult.ACCEPT)


class SwearingFilter(BaseFilter):
    """
    Filter for detecting swearing or profanity in text.
    """
    def __init__(self):
        """
        Initializes the SwearingFilter with the input text.

        Args:
            text (str): The text to be filtered.
        """
        super().__init__(filter_type="swearing")

    def apply(self, text) -> ModerationResult:
        """
        Applies the swearing filter to the text.

        Returns:
            ModerationResult: HIDE if swearing is detected, otherwise ACCEPT.
        """
        if any(word in text.lower() for word in self.offensive_words):
            logger.info(f"Swearing detected in comment: '{text}'")
            return ModerationResult(ModerationResult.HIDE)
        return ModerationResult(ModerationResult.ACCEPT)

class TappouhkausFilter(BaseFilter):
    """
    Filter for detecting threatening or violent language in text.
    """
    def __init__(self):
        """
        Initializes the TappouhkausFilter.
        """
        super().__init__(filter_type="tappouhkaus")
        
    def apply(self, text) -> ModerationResult:
        """
        Applies the tappouhkaus filter to the text.

        Returns:
            ModerationResult: BAN if threatening words are detected, otherwise ACCEPT.
        """
        if any(word in text.lower() for word in self.offensive_words):
            logger.info(f"Threatening language detected in comment: '{text}'")
            return ModerationResult(ModerationResult.BAN)
        return ModerationResult(ModerationResult.ACCEPT)

class FatPhobiaFilter(BaseFilter):
    """
    Filter for detecting fatphobic language in text.
    """
    def __init__(self):
        """
        Initializes the FatPhobiaFilter.
        """
        super().__init__(filter_type="fatphobia")

    def apply(self, text) -> ModerationResult:
        """
        Applies the fatphobia filter to the text.

        Returns:
            ModerationResult: BAN if offensive words are detected, otherwise ACCEPT.
        """
        if any(word in text.lower() for word in self.offensive_words):
            logger.info(f"Fatphobic content detected in comment: '{text}'")
            return ModerationResult(ModerationResult.BAN)
        return ModerationResult(ModerationResult.ACCEPT)

class SexualViolenceFilter(BaseFilter):
    """
    Filter for detecting sexual violence language in text.
    """
    def __init__(self):
        """
        Initializes the SexualViolenceFilter.
        """
        super().__init__(filter_type="sexual_violence")

    def apply(self, text) -> ModerationResult:
        """
        Applies the sexual violence filter to the text.

        Returns:
            ModerationResult: HUMAN_REVIEW if offensive words are detected, otherwise ACCEPT.
        """
        if any(word in text.lower() for word in self.offensive_words):
            logger.info(f"Sexual violence content detected in comment: '{text}'")
            return ModerationResult(ModerationResult.HUMAN_REVIEW)
        return ModerationResult(ModerationResult.ACCEPT)

class SexualHarassmentFilter(BaseFilter):
    """
    Filter for detecting sexual harassment language in text.
    """
    def __init__(self):
        """
        Initializes the SexualHarassmentFilter.
        """
        super().__init__(filter_type="sexual_harassment")

    def apply(self, text) -> ModerationResult:
        """
        Applies the sexual harassment filter to the text.

        Returns:
            ModerationResult: HUMAN_REVIEW if offensive words are detected, otherwise ACCEPT.
        """
        if any(word in text.lower() for word in self.offensive_words):
            logger.info(f"Sexual harassment content detected in comment: '{text}'")
            return ModerationResult(ModerationResult.HUMAN_REVIEW)
        return ModerationResult(ModerationResult.ACCEPT)

class PannaaksFilter(BaseFilter):
    """
    Filter for detecting 'pannaaks' or related sexual content in text.
    """
    def __init__(self):
        """
        Initializes the PannaaksFilter.
        """
        super().__init__(filter_type="pannaaks")

    def apply(self, text) -> ModerationResult:
        """
        Applies the pannaaks filter to the text.

        Returns:
            ModerationResult: HUMAN_REVIEW if offensive words are detected, otherwise ACCEPT.
        """
        if any(word in text.lower() for word in self.offensive_words):
            logger.info(f"Offensive content detected in comment: '{text}'")
            return ModerationResult(ModerationResult.HUMAN_REVIEW)
        return ModerationResult(ModerationResult.ACCEPT)

class BoyFilter(BaseFilter):
    """
    Filter for detecting references to being a boy in text.
    """
    def __init__(self):
        """
        Initializes the BoyFilter.
        """
        super().__init__(filter_type="boy")

    def apply(self, text) -> ModerationResult:
        """
        Applies the boy filter to the text.

        Returns:
            ModerationResult: BAN if references to being a boy are detected, otherwise ACCEPT.
        """
        if any(word in text.lower() for word in self.offensive_words):
            logger.info(f"Reference to being a boy detected in comment: '{text}'")
            return ModerationResult(ModerationResult.BAN)
        return ModerationResult(ModerationResult.ACCEPT)