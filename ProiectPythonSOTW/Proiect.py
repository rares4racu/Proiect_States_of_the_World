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

def find_government(ib, name):
    for row in ib.find_all("tr"):
        th = row.find("th")
        td = row.find("td")
        if th and td:
            header = th.get_text(" ").strip().lower()
            if re.match(r"^\bgovernment\b$", header):
                l = td.find_all("li")
                if l:
                    return clean_text(", ".join(li.get_text(" ", strip=True) for li in l))
                for c in td.find_all("span", class_="geo"):
                    c.decompose()
                return clean_text(td.get_text(" ").strip())
    return None


def remove_unwanted_capital(text):
    if not text:
        return None
    if text.lower() in ("none", "null", "n/a", ""):
        return None
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"[\xa0\u200b\u2060\ufeff]", " ", text)
    text = re.sub(r"\s+", " ", text)
    text_list = text.split()
    final_text = []
    for c in text_list:
        if c[0].isdigit():
            continue
        if c.startswith("/"):
            continue
        if len(c) == 1 and c[0] == "a":
            continue
        final_text.append(c)
    return " ".join(final_text)


def remove_unwanted_language(text):
    if not text:
        return None
    if text.lower() in ("none", "null", "n/a", ""):
        return None
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"[\xa0\u200b\u2060\ufeff]", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\b\d+(\.\d+)?%\b|\b\d+(\.\d+)?\b", "", text)
    text = re.sub(r" %", "",text)
    text = re.sub(r" • ", ", ", text)
    text = re.sub(r" a","",text)
    text = re.sub(r", plusny other languages so recognized by law","",text)
    return text.strip()


def remove_unwanted_rest(text):
    if not text:
        return None
    if text.lower() in ("none", "null", "n/a", ""):
        return None
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"[\xa0\u200b\u2060\ufeff]", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r" \)", "", text)
    return text.strip()


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


def normalize_country_name(name):
    name = name.lower()
    name = re.sub(r"\(.*?\)", "", name)
    name = name.replace("people's republic of", "")
    name = name.replace("republic of", "")
    name = name.replace("kingdom of", "")
    name = name.replace("state of", "")
    return name.strip()


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
        if not country_a:
            continue
        name = country_a.get_text(strip=True)
        if normalize_country_name(name) != normalize_country_name(country_name):
            continue
        neighbours_td = tds[5]
        neighbours = []
        for a in neighbours_td.find_all("a"):
            text = clean_text(a.get_text(strip=True))
            if not text:
                continue
            if "border" in text.lower():
                continue
            neighbours.append(text)

        if "Dahagram-Angarpota" in neighbours:
            neighbours.remove("Dahagram-Angarpota")
        if country_name == "Canada" and "Denmark" in neighbours:
            neighbours.remove("Denmark")
        if country_name == "India" and "Ram Setu" in neighbours:
            neighbours.remove("Ram Setu")
        if "Gaza Strip" in neighbours:
            neighbours.remove("Gaza Strip")
        if "West Bank" in neighbours:
            neighbours.remove("West Bank")
        if "state of Palestine" in neighbours:
            neighbours.remove("state of Palestine")

        return ", ".join(neighbours) if neighbours else None
    return None


def find_population(infobox):
    rows = infobox.find_all("tr")
    for i, row in enumerate(rows):
        th = row.find("th")
        if not th:
            continue
        header = th.get_text(" ", strip=True).lower()
        if "population" not in header:
            continue
        td = row.find("td")
        if not td and i + 1 < len(rows):
            td = rows[i + 1].find("td")
        if not td:
            continue
        text = clean_text(td.get_text(" ", strip=True)).lower()
        text = re.sub(r"\b\d+(st|nd|rd|th)\b", "", text)
        match = re.search(r"(\d+(?:[\.,]\d+)?)\s*(billion|million|m|b)", text, re.IGNORECASE)
        if match:
            value = float(match.group(1).replace(",", "."))
            unit = match.group(2).lower()
            if unit in ["b", "billion"]:
                return int(value * 1_000_000_000)
            else:
                return int(value * 1_000_000)

        if any(c in text for c in ["°", "′", "″"]):
            text = re.sub(r"\d[\d,]*", "", text)

        numbers = re.findall(r"\d[\d,]*", text)
        valid_numbers = []
        for n in numbers:
            n_int = int(n.replace(",", ""))
            if n_int < 100:
                continue
            if 1800 <= n_int <= 2100:
                continue
            if n_int < 50_000 and n_int != max(valid_numbers, default=n_int):
                continue
            valid_numbers.append(n_int)

        if valid_numbers:
            return max(valid_numbers)
    return None


def init_db():
    conn = sqlite3.connect("countries.db")
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


def check_db():
    conn = sqlite3.connect("countries.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM countries ORDER BY name;")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()

def get_top_10(field):
    conn = sqlite3.connect("countries.db")
    cursor = conn.cursor()
    cursor.execute(f"""
    SELECT name, {field} FROM countries
    WHERE {field} IS NOT NULL
    ORDER BY {field} DESC
    LIMIT 10;
    """)
    rows = cursor.fetchall()
    conn.close()
    return [{"name": name, field: value} for name, value in rows]


def scrape(country, soup_borders, conn):
    try:
        url = "https://en.wikipedia.org/wiki/" + quote(country)
        req_country = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        webpage_country = urlopen(req_country).read()
        soup_country = BeautifulSoup(webpage_country, "html.parser")

        country_name = soup_country.find("h1", id="firstHeading").text
        if country_name == "Georgia (country)":
            country_name = "Georgia"
        if country_name == "Republic of Ireland":
            country_name = "Ireland"
        if country_name == "Ivory Coast":
            country_name = "Côte d'Ivoire"
        if country_name == "Timor-Leste":
            country_name = "East Timor"
        infobox_country = soup_country.find("table", class_=lambda x: x and "infobox" in x)
        if not infobox_country:
            raise ValueError("Infobox not found")

        capital_raw = find_field(infobox_country, ["capital"])
        if country_name == "Liberia":
            capital_raw = "Monrovia"

        population = find_population(infobox_country)
        language_raw = find_field(infobox_country, ["language"])
        neighbours = get_neighbours(country_name, soup_borders)

        data = (
            country_name,
            remove_unwanted_capital(capital_raw),
            population,
            complete_density(infobox_country),
            complete_area(infobox_country),
            remove_unwanted_language(language_raw),
            remove_unwanted_rest(find_field(infobox_country, ["time zone"])),
            remove_unwanted_rest(find_government(infobox_country, ["government"])),
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

def delete_db():
    conn = sqlite3.connect("countries.db")
    cursor = conn.cursor()
    cursor.execute("""
    Delete FROM countries;
    """)
    conn.commit()
    conn.close()
def main():
    conn = init_db()
    url_borders = "https://en.wikipedia.org/wiki/List_of_countries_and_territories_by_number_of_land_borders"
    req_borders = Request(url_borders, headers={"User-Agent": "Mozilla/5.0"})
    webpage_borders = urlopen(req_borders).read()
    soup_borders = BeautifulSoup(webpage_borders, "html.parser")

    countries = get_all_countries(soup_borders)
    for country in countries:
        try:
            if country == "Georgia":
                country = "Georgia_(country)"
            if country == "Ireland":
                country = "Republic of Ireland"
            if country == "":
                continue
            scrape(country, soup_borders, conn)
        except Exception as e:
            print(f"Failed to scrape {country}: {e}")

    conn.close()
    check_db()


if __name__ == "__main__":
    main()
