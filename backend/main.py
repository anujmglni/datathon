from fastapi import FastAPI

app = FastAPI(title="KSP Crime Analytics API")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to the KSP Crime Analytics API"}
