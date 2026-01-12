import sqlite3
import unittest
from unittest.mock import patch, MagicMock
from ProiectPythonSOTW.Proiect_scraper import *


class TesterScraper(unittest.TestCase):

    def test_remove_ref(self):
        self.assertEqual(remove_ref("Romania[1][2][3]"), "Romania")

    def test_get_field_density(self):
        html = """
        <table class ="infobox">
            <tr>
                <th>Density</th>
                <td>79.9 d</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        infobox = soup.find("table")
        result = get_field(infobox, ["density"])
        self.assertEqual(result, '79.9 d')

    def test_get_field_area(self):
        html = """
        <table class ="infobox">
            <tr>
                <th>Total</th>
                <td>238397.0</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        infobox = soup.find("table")
        result = get_field(infobox, ["total"])
        self.assertEqual(result, '238397.0')

    def test_get_field_capital(self):
        html = """
        <table class ="infobox">
            <tr>
                <th>Capital</th>
                <td>Bucharest</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        infobox = soup.find("table")
        result = get_field(infobox, ["capital"])
        self.assertEqual(result, 'Bucharest')

    def test_get_field_language(self):
        html = """
        <table class ="infobox">
            <tr>
                <th>Language</th>
                <td>Romanian</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        infobox = soup.find("table")
        result = get_field(infobox, ["language"])
        self.assertEqual(result, 'Romanian')

    def test_get_field_time_zone(self):
        html = """
        <table class ="infobox">
            <tr>
                <th>Time zone</th>
                <td>UTC+2</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        infobox = soup.find("table")
        result = get_field(infobox, ["time zone"])
        self.assertEqual(result, 'UTC+2')

    def test_get_countries(self):
        html = """
        <table class ="wikitable sortable">
            <tr>
                <th>Country</th><th>Data</th>
            </tr>
            <tr>
                <td><a href="/wiki/Romania">Romania</a></td>
                <td></td><td></td><td></td><td></td><td></td>
            </tr>
            <tr>
                <td><a href="/wiki/Bulgaria">Bulgaria</a></td>
                <td></td><td></td><td></td><td></td><td></td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = get_countries(soup)
        self.assertEqual(result, ["Romania", "Bulgaria"])

    def test_remove_unwanted_capital(self):
        self.assertEqual(remove_unwanted_capital("Bucharest (information) \xa0 5 /d a "), "Bucharest")

    def test_get_population(self):
        html = """
        <table class ="infobox">
            <tr>
                <th>Population</th>
                <td>19036031</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        infobox = soup.find("table")
        result = get_population(infobox)
        self.assertEqual(result, 19036031)

    def test_get_density(self):
        html = """
        <table class ="infobox">
            <tr>
                <th>Density</th>
                <td>79.9 d</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        infobox = soup.find("table")
        result = get_density(infobox)
        self.assertEqual(result, 79.9)

    def test_get_area(self):
        html = """
        <table class ="infobox">
            <tr>
                <th>Total</th>
                <td>238397 d</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        infobox = soup.find("table")
        result = get_area(infobox)
        self.assertEqual(result, 238397.0)

    def test_remove_unwanted_language(self):
        self.assertEqual(remove_unwanted_language("Romanian (information)  \xa0"), "Romanian")

    def test_convert_timezone(self):
        self.assertEqual(convert_timezone("01:30"), 1.5)

    def test_remove_unwanted_timezone(self):
        self.assertEqual(remove_unwanted_timezone("UTC +1, UTC +2"), "UTC+1, UTC+2")

    def test_get_government(self):
        html = """
        <table class ="infobox">
            <tr>
                <th>Government</th>
                <td>Unitary semi-presidential republic [1][2][3]</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        infobox = soup.find("table")
        result = get_government(infobox)
        self.assertEqual(result, "Unitary semi-presidential republic")

    def test_remove_unwanted_government(self):
        self.assertEqual(remove_unwanted_government("Unitary semi-presidential republic (information)  ) \xa0"),
                         "Unitary semi-presidential republic")

    def test_normalize_country_name(self):
        self.assertEqual(normalize_country_name("people's republic of china"), "china")

    def test_get_neighbours(self):
        html = """
        <table class ="wikitable sortable">
            <tr>
                <th>Country</th><th>Data</th>
            </tr>
            <tr>
                <td><a href="/wiki/Romania">Romania</a></td>
                <td></td><td></td><td></td><td></td><td>
                <a>Bulgaria</a>
                <a>Hungary</a> 
                <a>Moldova</a> 
                <a>Serbia</a> 
                <a>Ukraine</a>
                </td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        result = get_neighbours("Romania", soup)
        self.assertEqual(result, "Bulgaria, Hungary, Moldova, Serbia, Ukraine")

    @patch("ProiectPythonSOTW.Proiect_scraper.urlopen")
    def test_scrape(self, mock_urlopen):
        country_html = b"""
                <h1 id="firstHeading">Romania</h1>
                <table class="infobox">
                    <tr><th>Capital</th><td>Bucharest</td></tr>
                    <tr><th>Population</th><td>19036031</td></tr>
                    <tr><th>Density</th><td>79.9</td></tr>
                    <tr><th>Total</th><td>238397</td></tr>
                    <tr><th>Language</th><td>Romanian</td></tr>
                    <tr><th>Time zone</th><td>UTC+2</td></tr>
                    <tr><th>Government</th><td>Unitary semi-presidential republic</td></tr>
                </table>
                """
        mock_response = MagicMock()
        mock_response.read.return_value = country_html
        mock_urlopen.return_value = mock_response
        borders_html = """
                <table class ="wikitable sortable">
                    <tr>
                        <th>Country</th><th>Data</th>
                    </tr>
                    <tr>
                        <td><a href="/wiki/Romania">Romania</a></td>
                        <td></td><td></td><td></td><td></td><td>
                        <a>Bulgaria</a>
                        <a>Hungary</a> 
                        <a>Moldova</a> 
                        <a>Serbia</a> 
                        <a>Ukraine</a>
                        </td>
                    </tr>
                </table>
             """
        soup = BeautifulSoup(borders_html, "html.parser")
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS countries (
                    name TEXT PRIMARY KEY NOT NULL,
                    capital TEXT,
                    population INTEGER NOT NULL,
                    density REAL,
                    area REAL,
                    language TEXT,
                    time_zone TEXT,
                    government TEXT,
                    neighbours TEXT
                );
            """)
        conn.commit()
        scrape("Romania", soup, conn)
        cursor.execute("SELECT * FROM countries WHERE name = 'Romania'")
        row = cursor.fetchone()
        self.assertEqual(row[0], "Romania")
        self.assertEqual(row[1], "Bucharest")
        self.assertEqual(row[2], 19036031)
        self.assertAlmostEqual(row[3], 79.9)
        self.assertAlmostEqual(row[4], 238397.0)
        self.assertEqual(row[5], "Romanian")
        self.assertEqual(row[6], "UTC+2")
        self.assertEqual(row[7], "Unitary semi-presidential republic")
        self.assertEqual(row[8], "Bulgaria, Hungary, Moldova, Serbia, Ukraine")
        conn.close()


if __name__ == '__main__':
    unittest.main()
