import sqlite3

# Funcție pentru crearea bazei de date.
def init_db():
    conn = sqlite3.connect("countries.db")
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
    cursor.execute("CREATE INDEX IF NOT EXISTS country_population ON countries (population);")
    cursor.execute("CREATE INDEX IF NOT EXISTS country_density ON countries (density);")
    cursor.execute("CREATE INDEX IF NOT EXISTS country_language ON countries (language);")
    cursor.execute("CREATE INDEX IF NOT EXISTS country_time_zone ON countries (time_zone);")
    cursor.execute("CREATE INDEX IF NOT EXISTS country_government ON countries (government);")
    cursor.execute("CREATE INDEX IF NOT EXISTS country_neighbours ON countries (neighbours);")
    conn.commit()
    return conn

# Funcție pentru a obține toate informațiile din baza de date.
def check_db():
    conn = sqlite3.connect("countries.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM countries ORDER BY name;")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()

# Funcție pentru a șterge toate informațiile din baza de date.
def delete_db():
    conn = sqlite3.connect("countries.db")
    cursor = conn.cursor()
    cursor.execute("""
    Delete FROM countries;
    """)
    conn.commit()
    conn.close()

# Funcție pentru a obține top 10 dintr-o anumită categorie (populație sau densitate).
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
