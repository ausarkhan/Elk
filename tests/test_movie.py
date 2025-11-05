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

    def test_empty_title_and_plot(self):
        m = Movie("", 5.0, "")
        j = m.to_json()
        self.assertEqual(j["title"], "")
        self.assertEqual(j["plot"], "")

    def test_rating_passed_as_numeric_string(self):
        m = Movie("S", "8.5", "p")
        j = m.to_json()
        # constructor coerces numeric-like strings to float
        self.assertIsInstance(j["rating"], float)
        self.assertEqual(j["rating"], 8.5)

    def test_rating_invalid_string_raises(self):
        with self.assertRaises(ValueError):
            Movie("Bad", "not-a-number", "p")

    def test_mutable_attributes_reflect_after_change(self):
        m = Movie("T", 6.0, "plot")
        m.title = "New Title"
        m.rating = 9.1
        m.plot = "New plot"
        j = m.to_json()
        self.assertEqual(j["title"], "New Title")
        self.assertEqual(j["rating"], 9.1)
        self.assertEqual(j["plot"], "New plot")

    def test_rating_zero_is_valid(self):
        m = Movie("Z", 0.0, "zero")
        j = m.to_json()
        self.assertEqual(j["rating"], 0.0)

    def test_large_rating_preserved(self):
        large = 1e308
        m = Movie("Big", large, "p")
        j = m.to_json()
        self.assertEqual(j["rating"], large)

    def test_types_in_to_json_when_correct_input(self):
        m = Movie("S", 4.2, "p")
        j = m.to_json()
        self.assertIsInstance(j["title"], str)
        self.assertIsInstance(j["rating"], float)
        self.assertIsInstance(j["plot"], str)

    def test_non_string_title_is_preserved(self):
        # implementation does not coerce title to str; it preserves whatever was passed
        m = Movie(12345, 7.0, "p")
        j = m.to_json()
        self.assertEqual(j["title"], 12345)


if __name__ == "__main__":
    unittest.main()
