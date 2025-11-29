from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"Analytics service is running."}
