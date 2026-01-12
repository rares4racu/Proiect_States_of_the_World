import unittest
from unittest.mock import patch
from ProiectPythonSOTW.Proiect_db import *


class TesterDB(unittest.TestCase):

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
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
            )
        """)
        self.cursor.execute("CREATE INDEX IF NOT EXISTS country_population ON countries(population)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS country_density ON countries(density)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS country_language ON countries(language)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS country_time_zone ON countries(time_zone)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS country_government ON countries(government)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS country_neighbours ON countries(neighbours)")
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_init_db(self):
        with patch("ProiectPythonSOTW.Proiect_db.sqlite3.connect", return_value=self.conn):
            conn = init_db()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='countries'")
            table = cursor.fetchone()
            self.assertIsNotNone(table)
            self.assertEqual(table[0], 'countries')
            indexes = ['country_population', 'country_density', 'country_language',
                       'country_time_zone', 'country_government', 'country_neighbours']
            for index in indexes:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index}'")
                self.assertIsNotNone(cursor.fetchone())

    def test_get_10_population(self):
        self.cursor.executemany("""
            INSERT INTO countries (name, capital, population, density, area, language, time_zone, government, neighbours)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            ("Romania", "Bucharest", 19036031, 79.9, 238397.0, "Romanian", "UTC+2",
             "Unitary semi-presidential republic", "Bulgaria, Hungary, Moldova, Serbia, Ukraine"),
            ("Germany", "Berlin", 83491249, 233.0, 357022.0, "German", "UTC+1", "Federal parliamentary republic",
             "Austria, Belgium, Czech Republic, Denmark, France, Luxembourg, Netherlands, Poland, Switzerland"),
            ("Moldova", "Chișinău", 2381325, 78.5, 33843.0, "Romanian", "UTC+2", "Unitary parliamentary republic",
             "Romania, Ukraine")
        ])
        self.conn.commit()

        with patch("ProiectPythonSOTW.Proiect_db.sqlite3.connect", return_value=self.conn):
            top_10_pop = get_top_10("population")
            self.assertEqual(top_10_pop[0]["name"], "Germany")
            self.assertEqual(top_10_pop[1]["name"], "Romania")
            self.assertEqual(top_10_pop[2]["name"], "Moldova")

    def test_get_10_density(self):
        self.cursor.executemany("""
            INSERT INTO countries (name, capital, population, density, area, language, time_zone, government, neighbours)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            ("Romania", "Bucharest", 19036031, 79.9, 238397.0, "Romanian", "UTC+2",
             "Unitary semi-presidential republic", "Bulgaria, Hungary, Moldova, Serbia, Ukraine"),
            ("Germany", "Berlin", 83491249, 233.0, 357022.0, "German", "UTC+1", "Federal parliamentary republic",
             "Austria, Belgium, Czech Republic, Denmark, France, Luxembourg, Netherlands, Poland, Switzerland"),
            ("Moldova", "Chișinău", 2381325, 78.5, 33843.0, "Romanian", "UTC+2", "Unitary parliamentary republic",
             "Romania, Ukraine")
        ])
        self.conn.commit()

        with patch("ProiectPythonSOTW.Proiect_db.sqlite3.connect", return_value=self.conn):
            top_10_density = get_top_10("density")
            self.assertEqual(top_10_density[0]["name"], "Germany")
            self.assertEqual(top_10_density[1]["name"], "Romania")
            self.assertEqual(top_10_density[2]["name"], "Moldova")


if __name__ == '__main__':
    unittest.main()
