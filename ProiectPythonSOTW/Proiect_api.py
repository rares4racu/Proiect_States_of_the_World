from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from Proiect_db import get_top_10
import sqlite3
import logging

# Pentru rulare trebuie să vă aflați în directorul proiectului și să rulați următoarea comandă (asigurați vă că aveți
# instalate toate librăriile necesare): uvicorn Proiect_api:app --reload
# Coduri erori :
# 400 -> Eroarea necunoscută.
# 404 -> Pagina nu există.
# 422 -> Parametri invalizi.
# 500 -> Problemă internă.


# Fișierul proiect.log reține toate request-urile și toate erorile
logging.basicConfig(
    filename='proiect.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="Proiect API")

# Middleware pentru logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    HTTP middleware that logs every HTTP request, and it's response status code.
    """
    logging.info(f"Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
    except Exception as e:
        logging.error(f"Error processing request {request.url}: {e}")
        raise e
    logging.info(f"Response status code: {response.status_code}")
    return response

# Exception handler în cazul în care nu există endpoint-ul.
@app.exception_handler(404)
async def page_not_found(request: Request, exc):
    """
    Handles errors raised when requested page doesn't exist.
    Returns an error message with status code 404.
    """
    logging.error(f"Endpoint not found: {request.url}")
    return JSONResponse({"message": f"Endpoint-ul {request.url.path} nu există."}, status_code=404)

# Exception handler în cazul în care parametrii introduși nu sunt valizi.
@app.exception_handler(RequestValidationError)
async def request_validation_error(request: Request, exc):
    """
    Handles validation errors raised when request parameters are invalid.
    Returns a detailed description of validation issues with status code 422.
    """
    logging.error(f"RequestValidationError: {request.url}:{exc}")
    return JSONResponse({"message": f"Parametri invalizi pentru {request.url.path}", "errors": exc.errors()},
                        status_code=422)

# Exception handler pentru erori neprevăzute.
@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc):
    """
    Handles unexpected exceptions.
    Returns a detailed description of the unhandled exception with status code 400.
    """
    logging.error(f"Unhandled exception: {request.url}:{exc}")
    return JSONResponse({"message": str(exc)}, status_code=400)


@app.get("/", response_class=HTMLResponse)
def homepage():
    """
    Main page of the application.
    Returns the main page containing links for top 10 population, top 10 density and access to countries based on
    specific parameters.
    """
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
    """
    Endpoint for getting top 10 population.
    Returns a table containing the top 10 countries based on population.
    """
    try:
        data = get_top_10("population")
    except Exception as e:
        logging.error(f"Error in top_10_population: {e}")
        return JSONResponse({"message": str(e), "errors": e.args})
    html = "<h2>Top 10 population</h2><table border='1'><tr><th>Country</th><th>Population</th></tr>"
    for d in data:
        html += f"<tr><td>{d['name']}</td><td>{d['population']:,}</td></tr>"
    html += "</table>"
    return HTMLResponse(content=html)


# Endpoint pentru top-10-density.
@app.get("/top-10-density")
def top_10_density():
    """
    Endpoint for getting top 10 density.
    Returns a table containing the top 10 countries based on density.
    """
    try:
        data = get_top_10("density")
    except Exception as e:
        logging.error(f"Error in top_10_density: {e}")
        return JSONResponse({"message": str(e), "errors": e.args})
    html = "<h2>Top 10 density</h2><table border='1'><tr><th>Country</th><th>Density</th></tr>"
    for d in data:
        html += f"<tr><td>{d['name']}</td><td>{d['density']:,}</td></tr>"
    html += "</table>"
    return HTMLResponse(content=html)


# Endpoint pentru a obține un tabel care conține țări în funcție de fusul orar, limba, forma de guvern și vecini.
@app.get("/countries")
def get_countries(time_zone: str | None = Query(default=None), language: str | None = Query(default=None),
                  government: str | None = Query(default=None), neighbours: str | None = Query(default=None)):
    """
    Get a tabel of countries filtered by optional criteria.
    This endpoint allows filtering countries by one or more of the following criteria:
    time zone, language, government and neighbours.
    Parameters:
        time_zone (str | None): Time zone used to filter the countries.
        language (str | None): Language used to filter the countries.
        government (str | None): Government used to filter the countries.
        neighbours (str | None): Neighbours used to filter the countries.
    Returns:
        HTMLResponse: An HTML table containing all matching countries and their details.
    Raises:
        HTTPException 500: If an internal server error occurs.
        HTTPException 422: If the parameters are invalid.
    """
    try:
        conn = sqlite3.connect("countries.db", check_same_thread=False)
    except Exception as e:
        logging.error(f"Error in get_countries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    if time_zone:
        filtered_rows = []
        for row in rows:
            tz_value = row[6]
            if tz_value:
                timezones = [tz.strip() for tz in tz_value.split(",")]
                if time_zone in timezones:
                    filtered_rows.append(row)
        rows = filtered_rows
    if not rows:
        logging.info(f"No countries found for query: time_zone={time_zone}, language = {language}, "
                     f"government={government}, neighbours={neighbours}")
        raise HTTPException(status_code=422, detail="Invalid parameters")
    html = "<h2>Countries</h2><table border='1'><tr>"
    headers = ["Country", "Capital", "Population", "Density", "Area", "Language", "Timezone", "Government",
               "Neighbours"]
    html += "".join(f"<th>{h}</th>" for h in headers)
    html += "</tr>"
    for row in rows:
        html += "<tr>"
        html += "".join(f"<td>{value}</td>" for value in row)
        html += "</tr>"
    html += "</table>"
    return HTMLResponse(content=html)