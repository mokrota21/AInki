import src
import os

def main():
    step = input("Login or Register? (l/r): ")
    if step == "r":
        # Register
        username = input("Enter your user username: ")
        password = input("Enter your user password: ")
        gmail = input("Enter your user gmail: ")
        userid = src.insert_user(gmail, password, username)

    elif step == "l":
        # Login
        username = input("Enter your user username or gmail: ")
        password = input("Enter your user password: ")
        userid = src.login(password, username)

    else:
        raise ValueError("Invalid step")

    # Upload file and process it
    path = os.path.abspath(input("Select a file to upload (absolute path): "))
    src.init_graph()
    with open(path, "rb") as f:
        file = src.DefaultReader().read_file(f)
    doc_id = src.insert_doc(file)
    chunks = src.DefaultChunker().chunk(file)
    objects = src.extract_objects_from_chunks(chunks, doc_id)
    src.insert_objects(objects)
    
    # Display file?

    # Track current page and merge new chunks

    # Check every minute for pending states

    # Pick random n objects from states and ask user. By ask I mean show one by one in popup window a) Name of the object b) chunks from chunk_s - x to chunk_e + x where x is constant variable
    # User can answer only by giving their own estimate of knowing the object. Answer must be true or false.
if __name__ == "__main__":
    main()
