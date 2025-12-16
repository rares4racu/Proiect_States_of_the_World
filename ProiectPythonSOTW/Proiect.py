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
                for c in td.find_all("span",class_="geo"):
                    c.decompose()
                return clean_text(td.get_text(" ").strip())
    return None

def remove_unwanted(text):
    if "Republic of Bulgaria" in text:
        return "Bulgaria"
    elif "Hellenic Republic" in text:
        return "Greece"
    elif "Republic of Indonesia" in text:
        return "Indonesia"
    elif "Republic of Türkiye" in text:
        return "Turkey"
    else:
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

def scrape(url):
    req = Request(url,headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    soup = BeautifulSoup(webpage, 'html.parser')
    country_name = soup.find("h1", id="firstHeading").text
    infobox = soup.find("table", class_="infobox")
    capital_raw = find_field(infobox, ["capital"])
    population_raw = find_field(infobox, ["estimate"])
    language_raw = find_field(infobox, ["language"])
    country = {
        "Name": country_name,
        "Capital": remove_unwanted(capital_raw),
        "Population": remove_unwanted(population_raw),
        "Density": complete_density(infobox),
        "Area": complete_area(infobox),
        "Language": remove_unwanted(language_raw),
        "Time zone": find_field(infobox, ["time zone"]),
        "Government": find_field(infobox, ["government"]),
    }
    return country

def get_country(name_country):
    template ="https://en.wikipedia.org/wiki/"
    url = template+name_country
    info=scrape(url)
    print(info)

countries = ["Romania","Bulgaria","Indonesia","Greece","Turkey","Japan"]
for country in countries:
    get_country(country)
