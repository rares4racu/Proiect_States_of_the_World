from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import re
from urllib.parse import quote


def clean_text(text):
    if not text:
        return None
    text = re.sub(r"\[[^\]]*\]", "", text).strip()
    return text


def get_field(ib, name):
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


def get_government(ib, name):
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
    text = re.sub(r" %", "", text)
    text = re.sub(r" • ", ", ", text)
    text = re.sub(r" a", "", text)
    text = re.sub(r", plusny other languages so recognized by law", "", text)
    return text.strip()


def remove_unwanted_others(text):
    if not text:
        return None
    if text.lower() in ("none", "null", "n/a", ""):
        return None
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"[\xa0\u200b\u2060\ufeff]", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r" \)", "", text)
    return text.strip()



def remove_unwanted_timezone(text):
    if not text:
        return None
    text = text.strip()
    if text.lower() in ("none", "null", "n/a", ""):
        return None
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"[\xa0\u200b\u2060\ufeff]", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r" Lunar Hijri calendar","",text)
    text = re.sub(r"–","-",text)
    text = re.sub(r"–","-",text)
    text = re.sub(r"- ", "-",text)
    text = re.sub(r"\+ ", "+",text)
    text = re.sub(r"±", "+", text)
    text = re.sub(r" / ",", ",text)
    text = re.sub(r"/", ", ", text)
    text = re.sub(r" and ", ", ", text)
    text = re.sub(r" \)", "", text)
    text = text.replace("UTC", "").replace(";", ",")
    text = text.replace("−", "-")

    parts = []
    for part in text.split(","):
        part = part.strip()
        if "to" in part:
            start, end = part.split("to")
            start = start.strip()
            end = end.strip()
            parts.append(start)
            parts.append(end)
        else:
            if part:
                parts.append(part)

    cleaned_offsets = []
    for o in parts:
        if ":" in o:
            h, m = o.split(":")
            offset = int(h) + int(m)/60
        else:
            offset = float(o)
        if offset >= 0 and not str(offset).startswith('+'):
            offset = f"+{offset}".rstrip('0').rstrip('.')
        else:
            offset = f"{offset}".rstrip('0').rstrip('.')
        cleaned_offsets.append(f"UTC {offset}")

    seen = set()
    result = []
    for c in cleaned_offsets:
        c = re.sub(r" \+","+",c)
        c = re.sub(r" -","-",c)
        if c not in seen:
            seen.add(c)
            result.append(c)
    return ', '.join(result) if result else "UTC+0"


def get_density(infobox):
    density_raw = get_field(infobox, ["density"])
    if not density_raw:
        return None
    density_raw = density_raw.replace(",", "")
    match = re.search(r"\d+(\.\d+)?", density_raw)
    return float(match.group()) if match else None


def get_area(infobox):
    area_raw = get_field(infobox, ["total"])
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


def get_countries(soup_borders):
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


def get_population(infobox):
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
        capital_raw = get_field(infobox_country, ["capital"])
        if country_name == "Liberia":
            capital_raw = "Monrovia"
        capital = remove_unwanted_capital(capital_raw)
        population = get_population(infobox_country)
        language_raw = get_field(infobox_country, ["language"])
        language = remove_unwanted_language(language_raw)
        neighbours = get_neighbours(country_name, soup_borders)

        data = (
            country_name,
            capital,
            population,
            get_density(infobox_country),
            get_area(infobox_country),
            language,
            remove_unwanted_timezone(get_field(infobox_country, ["time zone"])),
            remove_unwanted_others(get_government(infobox_country, ["government"])),
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
