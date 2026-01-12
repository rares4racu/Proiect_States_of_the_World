from fastapi import FastAPI,Query,Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse

from Proiect import get_top_10
import sqlite3

# Pentru rulare trebuie să vă aflați în directorul proiectului
# și să rulați următoarea comandă (asigurați vă că aveți instalate toate librăriile necesare, uitați vă in requirements_proiect): uvicorn Proiect_api:app --reload
app = FastAPI(title="Proiect API")

@app.exception_handler(404)
async def page_not_found(request: Request, exc):
    return JSONResponse({"message": f"Endpoint-ul {request.url.path} nu există."}, status_code=404)

@app.exception_handler(RequestValidationError)
async def request_validation_error(request: Request, exc):
    return JSONResponse({"message": f"Parametri invalizi pentru {request.url.path}","errors": exc.errors()})

@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc):
    return JSONResponse({"message": str(exc)}, status_code=500)

@app.get("/",response_class=HTMLResponse)
def homepage():
    return """
    <!DOCTYPE html>
    <html>
    <head>
    <title>Proiect API</title>
    <style>
    body {font-family:sans-serif; text-align:center; padding-top:50px; }
    input {padding-top:10px; margin: 10px; width: 200px; }
    button {
    margin: 20px;
    padding: 15px 30px;
    font-size : 16px;
    cursor: pointer;
    background-color: #4CAF50;
    color: white;
    transition: 0.3s;
    }
    button:hover {
    background-color: #45a049;
    }
    </style>
    </head>
    <body>
    <h1>Proiect API</h1>
    <button onclick="window.location.href='/top-10-population'">Top 10 population</button>
    <button onclick="window.location.href='/top-10-density'">Top 10 density</button>
    <form action="/countries" method="get">
       <input type="text" name="time_zone" placeholder="Time zone">
       <input type="text" name="language" placeholder="Language">
       <input type="text" name="government" placeholder="Government">
       <input type="text" name="neighbours" placeholder="Neighbour">
       <br>
       <button type="submit">Search</button>
    </form>    
    </body>
    </html>
    """
# Endpoint pentru top-10-population.
@app.get("/top-10-population")
def top_10_population():
    try:
        data = get_top_10("population")
    except Exception as e:
        return JSONResponse({"message": str(e), "errors": e.args})
    html = "<h2>Top 10 population</h2><table border='1'><tr><th>Country</th><th>Population</th></tr>"
    for d in data:
        html += f"<tr><td>{d['name']}</td><td>{d['population']:,}</td></tr>"
    html += "</table>"
    return HTMLResponse(content=html)

# Endpoint pentru top-10-density.
@app.get("/top-10-density")
def top_10_density():
    try:
        data = get_top_10("density")
    except Exception as e:
        return JSONResponse({"message": str(e), "errors": e.args})
    html = "<h2>Top 10 density</h2><table border='1'><tr><th>Country</th><th>Density</th></tr>"
    for d in data:
        html += f"<tr><td>{d['name']}</td><td>{d['density']:,}</td></tr>"
    html += "</table>"
    return HTMLResponse(content=html)

# Endpoint pentru a obține o listă de țări în funcție de fusul orar, limba, forma de guvern și vecini.
@app.get("/countries")
def get_countries(
        time_zone : str | None = Query(default=None),
        language : str | None = Query(default=None),
        government : str | None = Query(default=None),
        neighbours : str | None = Query(default=None),
):
    conn = sqlite3.connect("countries.db")
    cursor = conn.cursor()
    query = "SELECT * FROM countries WHERE 1=1"
    params = []
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
    if time_zone:
        filtered_rows =[]
        for row in rows:
            tz_value = row[6]
            if tz_value:
                timezones = [tz.strip() for tz in tz_value.split(",")]
                if time_zone in timezones:
                    filtered_rows.append(row)
        rows = filtered_rows
    if not rows:
        return JSONResponse(status_code=404, content={"message": "No countries found"})
    html = "<h2>Countries</h2><table border='1'><tr>"
    headers = ["Country", "Capital", "Population", "Density", "Area", "Language", "Timezone", "Government", "Neighbours"]
    html += "".join(f"<th>{h}</th>" for h in headers)
    html += "</tr>"
    for row in rows:
        html += "<tr>"
        html += "".join(f"<td>{value}</td>" for value in row)
        html += "</tr>"
    html += "</table>"
    return HTMLResponse(content=html)
