from fastapi import FastAPI
from pydantic import BaseModel

class BookBytes(BaseModel):
    name: str
    content: bytes
    size: float # in mb

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/add-book")
async def add_book(book: BookBytes):
    pass