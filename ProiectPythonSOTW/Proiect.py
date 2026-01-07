from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import re
import sqlite3
from urllib.parse import quote


def clean_text(text):
    if not text:
        return None
    text = re.sub(r"\[[^\]]*\]", "", text).strip()
    return text


def find_field(ib, name):
    for row in ib.find_all("tr"):
        th = row.find("th")
        td = row.find("td")
        if th and td:
            header = th.get_text(" ").strip().lower()
            if any(h in header for h in name):
                l = td.find_all("li")
                if l:
                    return clean_text(", ".join(li.get_text(" ", strip=True) for li in l))
                for c in td.find_all("span", class_="geo"):
                    c.decompose()
                return clean_text(td.get_text(" ").strip())
    return None


def remove_unwanted(text):
    if not text:
        return None
    return text.split(" ")[0]


def complete_density(infobox):
    density_raw = find_field(infobox, ["density"])
    if not density_raw:
        return None
    density_raw = density_raw.replace(",", "")
    match = re.search(r"\d+(\.\d+)?", density_raw)
    return float(match.group()) if match else None


def complete_area(infobox):
    area_raw = find_field(infobox, ["total"])
    if not area_raw:
        return None
    area_raw = area_raw.replace(",", "")
    match = re.search(r"\d+(\.\d+)?", area_raw)
    return float(match.group()) if match else None

def get_all_countries(soup_borders):
    table = soup_borders.find("table", class_="wikitable sortable")
    countries = []
    for row in table.find_all("tr"):
        tds = row.find_all("td")
        if len(tds) < 6:
            continue

        country_a = tds[0].find("a")
        if not country_a:
            continue
        name = country_a.get_text(strip=True)
        countries.append(name)

    return countries


def get_neighbours(country_name, soup_borders):
    table = soup_borders.find("table", class_="wikitable sortable")
    for row in table.find_all("tr"):
        tds = row.find_all("td")
        if len(tds) < 6:
            continue

        country_a = tds[0].find("a")
        name = country_a.get_text(strip=True)
        if name.lower() != country_name.lower():
            continue

        neighbours_td = tds[5]
        neighbours = []
        for a in neighbours_td.find_all("a"):
            text = a.get_text(strip=True)
            if re.fullmatch(r"\[[a-z]+\]", text.lower()):
                continue

            neighbours.append(text)
        return ", ".join(neighbours) if neighbours else None

    return None

def init_db():
    conn = sqlite3.connect('countries.db')
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS countries (
                name TEXT PRIMARY KEY,
                capital TEXT,
                population INTEGER,
                density REAL,
                area REAL,
                language TEXT,
                time_zone TEXT,
                government TEXT,
                neighbours TEXT
            );
        """)
    conn.commit()
    return conn


failed_countries = []
def scrape(country, soup_borders, conn):
    try:
        url = f"https://en.wikipedia.org/wiki/" + quote(country)
        req_country = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        webpage_country = urlopen(req_country).read()
        soup_country = BeautifulSoup(webpage_country, 'html.parser')
        country_name = soup_country.find("h1", id="firstHeading").text
        infobox_country = soup_country.find("table", class_="infobox")
        if not infobox_country:
            raise ValueError("Infobox not found")
        capital_raw = find_field(infobox_country, ["capital"])
        population_raw = find_field(infobox_country, ["estimate"],)
        population_text = remove_unwanted(population_raw)
        if population_text:
            match = re.search(r'\d+', population_text.replace(",", ""))
            population = int(match.group()) if match else None
        else:
            population = None
        language_raw = find_field(infobox_country, ["language"])
        neighbours = get_neighbours(country_name, soup_borders)

        data = (
            country_name,
            remove_unwanted(capital_raw),
            population,
            complete_density(infobox_country),
            complete_area(infobox_country),
            remove_unwanted(language_raw),
            find_field(infobox_country, ["time zone"]),
            find_field(infobox_country, ["government"]),
            neighbours
        )

        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO countries
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()
        print(f"Successfully added {country_name}!")
    except Exception as e:
        print(f"Failed to add {country}: {e}")
        failed_countries.append(country)

def check_db():
    conn = sqlite3.connect('countries.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM countries ORDER BY name;")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()

def main():
    conn = init_db()
    url_borders = "https://en.wikipedia.org/wiki/List_of_countries_and_territories_by_number_of_land_borders"
    req_borders = Request(url_borders, headers={'User-Agent': 'Mozilla/5.0'})
    webpage_borders = urlopen(req_borders).read()
    soup_borders = BeautifulSoup(webpage_borders, 'html.parser')
    countries = get_all_countries(soup_borders)
    for country in countries:
        try:
            scrape(country, soup_borders, conn)
        except Exception as e:
            print(f"Failed to scrape {country}: {e}")
    conn.close()
    check_db()
    if failed_countries:
        print(f"Failed to find {len(failed_countries)} countries!")
        for c in failed_countries:
            print(c)

if __name__ == "__main__":
    main()
