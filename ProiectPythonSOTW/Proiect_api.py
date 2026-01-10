from fastapi import FastAPI
from Proiect import get_top_10

app = FastAPI(title="Proiect API")

@app.get("/top-10-population")
def top_10_population():
    return get_top_10("population")

@app.get("/top-10-density")
def top_10_density():
    return get_top_10("density")