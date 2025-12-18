from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import re


def clean_text(text):
    text = re.sub(r'\[\w+', '', text)
    text = text.replace("\xa0", " ")
    return " ".join(text.split()).strip()


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
    return text.split(" ")[0]


def complete_density(infobox):
    density_raw = find_field(infobox, ["density"])
    density = remove_unwanted(density_raw)
    if "/km" in density:
        density_final = density + "^2"
    else:
        density_final = density + "/km^2"
    return density_final


def complete_area(infobox):
    area_raw = find_field(infobox, ["total"])
    area = remove_unwanted(area_raw)
    area_final = area + " km^2"
    return area_final


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


def scrape(url, url_borders):
    # Site-ul tarii
    req_country = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage_country = urlopen(req_country).read()
    soup_country = BeautifulSoup(webpage_country, 'html.parser')
    country_name = soup_country.find("h1", id="firstHeading").text
    infobox_country = soup_country.find("table", class_="infobox")
    capital_raw = find_field(infobox_country, ["capital"])
    population_raw = find_field(infobox_country, ["estimate"])
    language_raw = find_field(infobox_country, ["language"])
    # Site-ul granitelor
    req_borders = Request(url_borders, headers={'User-Agent': 'Mozilla/5.0'})
    webpage_borders = urlopen(req_borders).read()
    soup_borders = BeautifulSoup(webpage_borders, 'html.parser')
    neighbours = get_neighbours(country_name, soup_borders)

    country = {
        "Name": country_name,
        "Capital": remove_unwanted(capital_raw),
        "Population": remove_unwanted(population_raw),
        "Density": complete_density(infobox_country),
        "Area": complete_area(infobox_country),
        "Language": remove_unwanted(language_raw),
        "Time zone": find_field(infobox_country, ["time zone"]),
        "Government": find_field(infobox_country, ["government"]),
        "Neighbours": neighbours
    }
    return country


def get_country(name_country):
    template = "https://en.wikipedia.org/wiki/"
    url = template + name_country
    url_borders = "https://en.wikipedia.org/wiki/List_of_countries_and_territories_by_number_of_land_borders"
    info = scrape(url, url_borders)
    print(info)


countries = ["Romania", "Bulgaria", "Indonesia", "Greece", "Turkey", "Japan"]
for country in countries:
    get_country(country)
