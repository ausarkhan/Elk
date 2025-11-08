import unittest

from movie import Movie


class TestMovie(unittest.TestCase):
    def test_to_json_happy_path(self):
        m = Movie("Title", 7.5, "A plot")
        j = m.to_json()
        self.assertIsInstance(j, dict)
        self.assertEqual(j["title"], "Title")
        self.assertEqual(j["rating"], 7.5)
        self.assertEqual(j["plot"], "A plot")

    def test_rating_none(self):
        m = Movie("NoRating", None, "No plot")
        j = m.to_json()
        # rating should be None when initialized with None
        self.assertIsNone(j["rating"])


if __name__ == "__main__":
    unittest.main()
import unittest

from movie import Movie


class TestMovie(unittest.TestCase):
    def test_to_json_happy_path(self):
        m = Movie("Title", 7.5, "A plot")
        j = m.to_json()
        self.assertIsInstance(j, dict)
        self.assertEqual(j["title"], "Title")
        self.assertEqual(j["rating"], 7.5)
        self.assertEqual(j["plot"], "A plot")

    def test_rating_none(self):
        m = Movie("NoRating", None, "No plot")
        j = m.to_json()
        # rating should be None when initialized with None
        self.assertIsNone(j["rating"])


if __name__ == "__main__":
    unittest.main()
