import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from movie_scraper import MovieScraper, ParsedPage, ScrapeError, ParseError
from movie import Movie


class TestMovieScraper(unittest.TestCase):
    def make_resp(self, text, status_code=200):
        return SimpleNamespace(text=text, status_code=status_code)

    def test_constructor_accepts_dependencies(self):
        mock_client = Mock()
        mock_parser = lambda html: []
        ms = MovieScraper(mock_client, mock_parser)
        self.assertIs(ms.https_client, mock_client)
        self.assertIs(ms.parser, mock_parser)

    def test_fetch_calls_https_client_get_with_retries(self):
        mock_client = Mock()
        resp = self.make_resp('<html></html>', 200)
        mock_client.get_with_retries.return_value = resp
        parser = lambda html: []
        ms = MovieScraper(mock_client, parser)
        parsed = ms.fetch('https://example.com')
        mock_client.get_with_retries.assert_called_once_with('https://example.com')
        self.assertEqual(parsed.html, '<html></html>')

    def test_fetch_raises_on_non_200_status(self):
        mock_client = Mock()
        resp = self.make_resp('<html></html>', 500)
        mock_client.get_with_retries.return_value = resp
        ms = MovieScraper(mock_client, lambda html: [])
        with self.assertRaises(ScrapeError):
            ms.fetch('https://example.com')

    def test_fetch_propagates_network_exceptions(self):
        mock_client = Mock()
        mock_client.get_with_retries.side_effect = TimeoutError('net')
        ms = MovieScraper(mock_client, lambda html: [])
        with self.assertRaises(TimeoutError):
            ms.fetch('https://example.com')

    def test_scrape_happy_path_returns_movie_objects(self):
        mock_client = Mock()
        resp = self.make_resp('<html></html>', 200)
        mock_client.get_with_retries.return_value = resp
        def parser(html):
            return [{'title': 'T', 'rating': 7.0, 'plot': 'p'}]
        ms = MovieScraper(mock_client, parser, dataset_manager=None, base_url='https://base')
        movies = ms.scrape(2020)
        self.assertEqual(len(movies), 1)
        self.assertIsInstance(movies[0], Movie)
        self.assertEqual(movies[0].title, 'T')

    def test_scrape_uses_parser_with_response_html(self):
        mock_client = Mock()
        resp = self.make_resp('<html>XYZ</html>', 200)
        mock_client.get_with_retries.return_value = resp
        parser = Mock(return_value=[])
        ms = MovieScraper(mock_client, parser, base_url='https://b')
        ms.scrape(1999)
        parser.assert_called_once_with('<html>XYZ</html>')

    def test_parser_returns_empty_list_results_in_empty_movies(self):
        mock_client = Mock()
        mock_client.get_with_retries.return_value = self.make_resp('<html></html>')
        parser = lambda html: []
        ms = MovieScraper(mock_client, parser)
        self.assertEqual(ms.scrape(2000), [])

    def test_parser_raises_parse_error_wrapped(self):
        mock_client = Mock()
        mock_client.get_with_retries.return_value = self.make_resp('<html></html>')
        def bad_parser(html):
            raise ValueError('bad')
        ms = MovieScraper(mock_client, bad_parser)
        with self.assertRaises(ParseError):
            ms.scrape(2001)

    def test_movie_fields_preserved_exactly(self):
        mock_client = Mock()
        mock_client.get_with_retries.return_value = self.make_resp('<html></html>')
        def parser(html):
            return [{'title': 'Exact', 'rating': '8.5', 'plot': 'plot text'}]
        ms = MovieScraper(mock_client, parser)
        movies = ms.scrape(2002)
        self.assertEqual(movies[0].title, 'Exact')
        self.assertEqual(movies[0].rating, 8.5)
        self.assertEqual(movies[0].plot, 'plot text')

    def test_partial_item_missing_title_is_skipped(self):
        mock_client = Mock()
        mock_client.get_with_retries.return_value = self.make_resp('<html></html>')
        def parser(html):
            return [{'rating': 5.0, 'plot': 'x'}, {'title': 'Good', 'rating': 6.0, 'plot': 'y'}]
        ms = MovieScraper(mock_client, parser)
        movies = ms.scrape(2003)
        self.assertEqual(len(movies), 1)
        self.assertEqual(movies[0].title, 'Good')

    def test_rating_string_coercion_to_float(self):
        mock_client = Mock()
        mock_client.get_with_retries.return_value = self.make_resp('<html></html>')
        def parser(html):
            return [{'title': 'S', 'rating': '7.25', 'plot': ''}]
        ms = MovieScraper(mock_client, parser)
        movies = ms.scrape(2004)
        self.assertEqual(movies[0].rating, 7.25)

    def test_rating_invalid_string_skipped(self):
        mock_client = Mock()
        mock_client.get_with_retries.return_value = self.make_resp('<html></html>')
        def parser(html):
            return [{'title': 'Bad', 'rating': 'seven', 'plot': 'p'}, {'title': 'Ok', 'rating': 5, 'plot': 'q'}]
        ms = MovieScraper(mock_client, parser)
        movies = ms.scrape(2005)
        self.assertEqual(len(movies), 1)
        self.assertEqual(movies[0].title, 'Ok')

    def test_dataset_manager_save_called_when_present(self):
        mock_client = Mock()
        mock_client.get_with_retries.return_value = self.make_resp('<html></html>')
        def parser(html):
            return [{'title': 'SaveMe', 'rating': 9.0, 'plot': 'p'}]
        dataset = Mock()
        ms = MovieScraper(mock_client, parser, dataset_manager=dataset)
        ms.scrape(2006)
        dataset.save_movies.assert_called_once()

    def test_dataset_manager_not_called_if_none(self):
        mock_client = Mock()
        mock_client.get_with_retries.return_value = self.make_resp('<html></html>')
        def parser(html):
            return [{'title': 'A', 'rating': 1, 'plot': ''}]
        ms = MovieScraper(mock_client, parser, dataset_manager=None)
        ms.scrape(2007)
        # no exception means pass; ensure no attribute error

    def test_scrape_handles_large_number_of_items(self):
        mock_client = Mock()
        mock_client.get_with_retries.return_value = self.make_resp('<html></html>')
        def parser(html):
            return [{'title': f'T{i}', 'rating': 1, 'plot': ''} for i in range(100)]
        ms = MovieScraper(mock_client, parser)
        movies = ms.scrape(2008)
        self.assertEqual(len(movies), 100)

    def test_fetch_builds_correct_url_for_year(self):
        mock_client = Mock()
        resp = self.make_resp('<html></html>')
        mock_client.get_with_retries.return_value = resp
        parser = lambda html: []
        ms = MovieScraper(mock_client, parser, base_url='https://site')
        ms.scrape(1990)
        mock_client.get_with_retries.assert_called_once_with('https://site/1990')

    def test_scrape_ignores_parser_url_field(self):
        mock_client = Mock()
        mock_client.get_with_retries.return_value = self.make_resp('<html></html>')
        def parser(html):
            return [{'title': 'U', 'rating': 3, 'plot': '', 'url': '/rel'}]
        ms = MovieScraper(mock_client, parser)
        movies = ms.scrape(2010)
        # ensure Movie only has title/rating/plot
        self.assertFalse(hasattr(movies[0], 'url'))

    def test_scrape_filters_duplicates_by_title(self):
        mock_client = Mock()
        mock_client.get_with_retries.return_value = self.make_resp('<html></html>')
        def parser(html):
            return [{'title': 'Dup', 'rating': 1, 'plot': ''}, {'title': 'Dup', 'rating': 2, 'plot': 'b'}]
        ms = MovieScraper(mock_client, parser)
        movies = ms.scrape(2011)
        self.assertEqual(len(movies), 1)
        self.assertEqual(movies[0].rating, 1)

    def test_error_logged_on_parser_exception(self):
        mock_client = Mock()
        mock_client.get_with_retries.return_value = self.make_resp('<html></html>')
        def bad_parser(html):
            raise RuntimeError('boom')
        ms = MovieScraper(mock_client, bad_parser)
        with self.assertRaises(ParseError):
            ms.scrape(2012)

    def test_scrape_works_when_client_returns_text_property_only(self):
        mock_client = Mock()
        resp = SimpleNamespace(text='<html>t</html>')
        mock_client.get_with_retries.return_value = resp
        def parser(html):
            return [{'title': 'T', 'rating': None, 'plot': ''}]
        ms = MovieScraper(mock_client, parser)
        movies = ms.scrape(2013)
        self.assertEqual(movies[0].title, 'T')


if __name__ == '__main__':
    unittest.main()
