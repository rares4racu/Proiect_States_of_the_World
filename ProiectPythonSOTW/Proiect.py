from Proiect_db import *
from Proiect_scraper import *


# Funcția principala pentru scraper.
def main():
    conn = init_db()
    url_borders = "https://en.wikipedia.org/wiki/List_of_countries_and_territories_by_number_of_land_borders"
    req_borders = Request(url_borders, headers={"User-Agent": "Mozilla/5.0"})
    webpage_borders = urlopen(req_borders).read()
    soup_borders = BeautifulSoup(webpage_borders, "html.parser")

    countries = get_countries(soup_borders)
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
