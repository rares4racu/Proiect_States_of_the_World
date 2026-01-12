import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi.testclient import TestClient
from ProiectPythonSOTW.Proiect_api import app
import sqlite3
from unittest.mock import patch



class TesterAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE countries (
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
        self.patcher = patch("ProiectPythonSOTW.Proiect_api.sqlite3.connect", return_value=self.conn)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.conn.close()

    def test_top_10_population(self):
        response = self.client.get("/top-10-population")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Germany", response.text)
        self.assertIn("Romania", response.text)
        self.assertIn("Moldova", response.text)

    def test_top_10_density(self):
        response = self.client.get("/top-10-density")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Germany", response.text)
        self.assertIn("Romania", response.text)
        self.assertIn("Moldova", response.text)

    def test_countries_filter_language(self):
        response = self.client.get("/countries?language=Romanian")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Romania", response.text)
        self.assertIn("Moldova", response.text)
        self.assertNotIn("Germany", response.text)

    def test_countries_filter_time_zone(self):
        response = self.client.get("/countries?time_zone=UTC%2B2")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Romania", response.text)
        self.assertIn("Moldova", response.text)
        self.assertNotIn("Germany", response.text)

    def test_countries_no_result(self):
        response = self.client.get("/countries?language=French")
        self.assertEqual(response.status_code, 500)
        self.assertIn("No countries found", response.text)

    def test_homepage(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Proiect API", response.text)


if __name__ == "__main__":
    unittest.main()
