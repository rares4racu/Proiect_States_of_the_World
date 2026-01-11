from fastapi import FastAPI,Query
from Proiect import get_top_10
import sqlite3

app = FastAPI(title="Proiect API")

@app.get("/top-10-population")
def top_10_population():
    return get_top_10("population")

@app.get("/top-10-density")
def top_10_density():
    return get_top_10("density")

@app.get("/countries")
def get_countries(
        time_zone : str | None = Query(default=None),
        language : str | None = Query(default=None),
        government : str | None = Query(default=None),
        neighbours : str | None = Query(default=None),
):
    conn = sqlite3.connect("countries.db")
    cursor = conn.cursor()
    query = "SELECT name,capital,population,density,area FROM countries WHERE 1=1"
    params = []
    if time_zone:
        time_zone = time_zone.replace(" ", "+")
        query += " AND time_zone LIKE ?"
        params.append(f"%{time_zone}%")
    if language:
        query += " AND language LIKE ?"
        params.append(f"%{language}%")
    if government:
        query += " AND government LIKE ?"
        params.append(f"%{government}%")
    if neighbours:
        query += " AND neighbours LIKE ?"
        params.append(f"%{neighbours}%")
    cursor.execute(query,params)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "name": r[0],
            "capital" : r[1],
            "population" : r[2],
            "density" : r[3],
            "area" : r[4],
        }
        for r in rows
    ]