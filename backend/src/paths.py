import os

src_path = os.path.dirname(__file__)
backend_path = os.path.dirname(src_path)
output_path = os.path.join(backend_path, "output")
upload_path = os.path.join(backend_path, "uploads")

if not os.path.exists(output_path):
    os.makedirs(output_path)

if not os.path.exists(upload_path):
    os.makedirs(upload_path)

def get_output_folder(doc_name: str, backend: str = None):
    backend = backend.split("/")[-1] if backend is not None else None
    name = os.path.splitext(os.path.basename(doc_name))[0]
    cur_path = os.path.join(output_path, name)
    ranks = ["auto", "vlm", "txt"]
    if backend is None:
        for rank in ranks:
            if os.path.exists(os.path.join(cur_path, rank)):
                backend = rank
                break
    if backend is None:
        subdirs = [d for d in os.listdir(cur_path) if os.path.isdir(os.path.join(cur_path, d))]
        backend = subdirs[0]
    return os.path.join(cur_path, backend)

def make_content_path(doc_name: str, backend: str = None):
    name = os.path.splitext(os.path.basename(doc_name))[0]
    return os.path.join(get_output_folder(doc_name, backend), name + "_content_list.json")
