import unittest
from results import ModerationResult
from filters import (HomoPhobiaFilter, JesusFilter, RacismFilter, SuicideFilter, 
                     SwearingFilter, TappouhkausFilter, FatPhobiaFilter, 
                     InclusiveSafetyFilter, SexualViolenceFilter, 
                     SexualHarassmentFilter, PannaaksFilter, BoyFilter)

class TestFilters(unittest.TestCase):

    def setUp(self):
        """Create instances of each filter before each test."""
        self.filters = {
            "homophobia": HomoPhobiaFilter(),
            "jesus": JesusFilter(),
            "racism": RacismFilter(),
            "suicide": SuicideFilter(),
            "swearing": SwearingFilter(),
            "tappouhkaus": TappouhkausFilter(),
            "fatphobia": FatPhobiaFilter(),
            "inclusive_safety": InclusiveSafetyFilter(),
            "sexual_violence": SexualViolenceFilter(),
            "sexual_harassment": SexualHarassmentFilter(),
            "pannaaks": PannaaksFilter(),
            "boy": BoyFilter(),
        }

    def test_homophobia_filter(self):
        filter_instance = self.filters["homophobia"]
        self.assertEqual(int(filter_instance.apply("You are a homo.")), ModerationResult.HUMAN_REVIEW)
        self.assertEqual(int(filter_instance.apply("You are nice.")), ModerationResult.ACCEPT)

    def test_jesus_filter(self):
        filter_instance = self.filters["jesus"]
        self.assertEqual(int(filter_instance.apply("Jesus is my savior.")), ModerationResult.HUMAN_REVIEW)
        self.assertEqual(int(filter_instance.apply("I like apples.")), ModerationResult.ACCEPT)

    def test_racism_filter(self):
        filter_instance = self.filters["racism"]
        self.assertEqual(int(filter_instance.apply("That neekeri should leave.")), ModerationResult.BAN)
        self.assertEqual(int(filter_instance.apply("All people are equal.")), ModerationResult.ACCEPT)

    def test_suicide_filter(self):
        filter_instance = self.filters["suicide"]
        self.assertEqual(int(filter_instance.apply("I want to commit suicide.")), ModerationResult.HUMAN_REVIEW)
        self.assertEqual(int(filter_instance.apply("I enjoy life.")), ModerationResult.ACCEPT)

    def test_swearing_filter(self):
        filter_instance = self.filters["swearing"]
        self.assertEqual(int(filter_instance.apply("You are such a perkele.")), ModerationResult.HIDE)
        self.assertEqual(int(filter_instance.apply("Good morning.")), ModerationResult.ACCEPT)

    def test_tappouhkaus_filter(self):
        filter_instance = self.filters["tappouhkaus"]
        self.assertEqual(int(filter_instance.apply("I will kill you.")), ModerationResult.BAN)
        self.assertEqual(int(filter_instance.apply("Have a nice day.")), ModerationResult.ACCEPT)

    def test_fatphobia_filter(self):
        filter_instance = self.filters["fatphobia"]
        self.assertEqual(int(filter_instance.apply("You are so fat.")), ModerationResult.BAN)
        self.assertEqual(int(filter_instance.apply("You are healthy.")), ModerationResult.ACCEPT)

    def test_inclusive_safety_filter(self):
        filter_instance = self.filters["inclusive_safety"]
        self.assertEqual(int(filter_instance.apply("You are a homo.")), ModerationResult.HUMAN_REVIEW)
        self.assertEqual(int(filter_instance.apply("Good day to you.")), ModerationResult.ACCEPT)

    def test_sexual_violence_filter(self):
        filter_instance = self.filters["sexual_violence"]
        self.assertEqual(int(filter_instance.apply("I experienced sexual violence.")), ModerationResult.HUMAN_REVIEW)
        self.assertEqual(int(filter_instance.apply("Everything is fine.")), ModerationResult.ACCEPT)

    def test_sexual_harassment_filter(self):
        filter_instance = self.filters["sexual_harassment"]
        self.assertEqual(int(filter_instance.apply("That was harassment.")), ModerationResult.HUMAN_REVIEW)
        self.assertEqual(int(filter_instance.apply("Let's play soccer.")), ModerationResult.ACCEPT)

    def test_pannaaks_filter(self):
        filter_instance = self.filters["pannaaks"]
        self.assertEqual(int(filter_instance.apply("Let's pannaaks tonight.")), ModerationResult.HUMAN_REVIEW)
        self.assertEqual(int(filter_instance.apply("It's a sunny day.")), ModerationResult.ACCEPT)

    def test_boy_filter(self):
        filter_instance = self.filters["boy"]
        self.assertEqual(int(filter_instance.apply("I am a boy.")), ModerationResult.BAN)
        self.assertEqual(int(filter_instance.apply("I am a girl.")), ModerationResult.ACCEPT)

if __name__ == "__main__":
    unittest.main()
