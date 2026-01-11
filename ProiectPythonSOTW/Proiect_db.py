import sqlite3

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

def delete_db():
    conn = sqlite3.connect("countries.db")
    cursor = conn.cursor()
    cursor.execute("""
    Delete FROM countries;
    """)
    conn.commit()
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
