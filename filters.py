from results import ModerationResult
import requests
import logging
import json
import os

# Set up logging
logger = logging
class BaseFilter:
    """
    Base class for all text filters.
    """

    BASE_UPDATE_URL = "https://updates.haspde.luova.club/filters"  # Base update URL for all filters

    def __init__(self, filter_type: str):
        self.offensive_words = []
        self.filter_type = filter_type
        self.local_version = self.load_local_version()  # Load local version
        self.update_url = f"{self.BASE_UPDATE_URL}/{filter_type}"
        self.version_url = f"{self.update_url}/version"
        
        # Update the word list
        self.update_word_list()
        
        # Load offensive words from local file
        self.load_offensive_words()

    def load_local_version(self) -> str:
        """
        Loads the local version of the word list from a JSON file.
        """
        try:
            with open(f"filters/{self.filter_type}_version.json", "r") as f:
                return json.load(f).get("version", "0")
        except FileNotFoundError:
            logger.info(f"No local version found for {self.filter_type}. Setting to 0.")
            return "0"

    def update_word_list(self):
        """Fetches the updated word list from the server if a newer version is available."""
        try:
            response = requests.get(self.version_url)
            response.raise_for_status()
            server_version = response.text.strip()

            if server_version != self.local_version:
                logger.info(f"Updating {self.filter_type} word list from {self.update_url}...")
                word_list_response = requests.get(self.update_url)
                word_list_response.raise_for_status()

                self.offensive_words = word_list_response.json().get("words", [])
                self.save_word_list()  # Save to local file
                self.save_local_version(server_version)  # Update version
                logger.info(f"Updated {self.filter_type} word list: {self.offensive_words[:10]}...")
            else:
                logger.info(f"{self.filter_type.capitalize()} word list is up to date.")

        except Exception as e:
            logger.error(f"Failed to update {self.filter_type} word list: {e}")

    def load_offensive_words(self):
        """Loads the offensive words list from a local JSON file."""
        try:
            with open(f"filters/{self.filter_type}_words.json", "r") as f:
                self.offensive_words = json.load(f).get("words", [])
                logger.info(f"Loaded {self.filter_type} offensive words: {self.offensive_words[:10]}...")
        except FileNotFoundError:
            logger.info(f"No local words file found for {self.filter_type}. Keeping the list empty.")

    def save_word_list(self):
        """Saves the offensive words list to a local file."""
        os.makedirs("filters", exist_ok=True)
        with open(f"filters/{self.filter_type}_words.json", "w") as f:
            json.dump({"words": self.offensive_words}, f)
        logger.info(f"Saved {self.filter_type} word list to {self.filter_type}_words.json")

    def save_local_version(self, version: str):
        """Saves the local version of the word list."""
        with open(f"filters/{self.filter_type}_version.json", "w") as f:
            json.dump({"version": version}, f)
        logger.info(f"Saved local version for {self.filter_type}: {version}")

    def apply(self, text) -> ModerationResult:
        """
        Applies the filter logic to the input text.

        Returns:
            ModerationResult: Result of the moderation, indicating the action to be taken (e.g., BAN, ACCEPT).
        """
        raise NotImplementedError("Subclasses should implement this method.")
    
class CustomFilter(BaseFilter):
    """Custom filter"""

    def __init__(self, filter_type="custom", _0_action: 'ModerationResult' = ModerationResult.ACCEPT, _1_action: 'ModerationResult' = ModerationResult.HIDE):
        if not _0_action is None:
            self._0_action = _0_action  # Action to take if no offensive words found
        else:
            self._0_action = ModerationResult.ACCEPT
        
        if not _1_action is None:
            self._1_action = _1_action  # Action to take if offensive words found

        else:
            self._1_action = ModerationResult.HIDE

        super().__init__(filter_type=filter_type)  # Call the base class constructor

    def apply(self, text) -> ModerationResult:
        """
        Applies custom filter logic to the input text.

        Returns:
            ModerationResult: Result of the moderation, indicating the action to be taken (e.g., BAN, ACCEPT).
        """
        # Check if the text contains any offensive words
        if any(word in text.lower() for word in self.offensive_words):
            logger.info(f"Filter detected offensive content in comment: '{text}'")
            return self._1_action  # Return the action for offensive words
        
        logger.info(f"No offensive content detected in comment: '{text}'")
        return self._0_action  # Return the action for non-offensive content


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


class JesusFilter(BaseFilter):
    """
    Filter for detecting jesus related stuff in text.
    """

    def __init__(self):
        """
        Initializes the JesusFilter with the input text.

        Args:
            text (str): The text to be filtered.
        """
        super().__init__(filter_type="jesus")

    def apply(self, text) -> ModerationResult:
        """
        Applies the jesus filter to the text.

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


class InclusiveSafetyFilter(BaseFilter):
    """
    Filter for detecting offensive language in text.
    """

    def __init__(self):
        """
        Initializes the InclusiveSafetyFilter.
        """
        super().__init__(filter_type="inclusive_safety")
        self.offensive_words = [
            # Homophobia
            "homo",
            "lesbo",
            "pervo",
            "hintti",
            "kurja",
            "tuhlaajapoika",
            "sukupuolihäiriö",
            "et oo ihminen",
            "turpakii",
            "gay",
            "queer",
            "biphobia",
            "transphobia",
            # Racism
            "neekeri",
            "ulkomaalainen",
            "mustalainen",
            "arjalainen",
            "musta",
            "ruisku",
            "racial slur",
            "xenophobia",
            "ethnic cleansing",
            "stereotype",
            # Suicide and Mental Health
            "itsemurha",
            "tapa itsesi",
            "kuolema",
            "apua",
            "toivoton",
            "masennus",
            "itsensä vahingoittaminen",
            "paha olo",
            "viiltää",
            "syrjäytyminen",
            "crazy",
            "insane",
            "mental case",
            "messed up",
            "depression",
            "anxiety",
            "panic",
            "therapy",
            "counseling",
            # Swearing and Aggression
            "perkele",
            "helvetti",
            "vittu",
            "paskaa",
            "saatana",
            "haista",
            "kusi",
            "tuhota",
            "hyökkäys",
            "väkivalta",
            "satuttaa",
            "ampua",
            "tappaa",
            "f***",
            "sh*t",
            "b*tch",
            "d*ck",
            # Fatphobia and Body Shaming
            "fat",
            "obese",
            "chubby",
            "overweight",
            "ugly",
            "disgusting",
            "lame",
            "skinny",
            "too thin",
            "too big",
            "paksu",
            "lihava",
            "olet ruma",
            "fatphobia",
            "body shaming",
            "weight shaming",
            # Misogyny and Gender Discrimination
            "bitch",
            "slut",
            "whore",
            "feminazi",
            "hysteria",
            "pussy",
            "naisen paikka",
            "misogyny",
            "sexism",
            "mansplaining",
            "objectify",
            # Xenophobia
            "immigrant",
            "foreigner",
            "refugee",
            "alien",
            "non-native",
            "cultural appropriation",
            "ethnic slurs",
            "othering",
            # Cultural Appropriation
            "cultural theft",
            "mocking culture",
            "stereotypes",
            "exotic",
            "white savior",
            "tokenism",
            # Environmental Neglect
            "climate change denial",
            "pollution",
            "wasteful",
            "greed",
            "deforestation",
            "carbon footprint",
            "environmental justice",
            # Religious Extremism
            "fanatic",
            "extremist",
            "cult",
            "indoctrination",
            "holy war",
            "intolerance",
            "proselytizing",
            # Trolling and Cyberbullying
            "troll",
            "harassment",
            "bully",
            "nettirosvo",
            "cyberbully",
            "doxxing",
            "threat",
            "intimidation",
            # Fun and Playful Additions
            "middle finger",
            "🖕",
            "screw you",
            "whatever",
            "shoo",
            "buzz off",
            "not cool",
            "bye felicia",
        ]

    def apply(self, text, training=True) -> ModerationResult:
        """
        Applies the inclusive safety filter to the text.

        Returns:
            ModerationResult: HUMAN_REVIEW if offensive words are detected, otherwise ACCEPT.
        """
        if any(word in text.lower() for word in self.offensive_words):
            logger.info(f"Offensive content detected in comment: '{text}'")
            return ModerationResult(
                ModerationResult.HUMAN_REVIEW
                if not training
                else ModerationResult.REMOVE
            )
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
