# server.py
from fastapi import FastAPI
from tool import main  # tool.py đã expose main từ main.py

app = FastAPI()

#GetID by passportNUmber

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/run")
def run():
    main()
    return {"ok": True}