from src import store_file

with open("uploads/1664976801.pdf", "rb") as f:
    print(store_file(5, f))