import subprocess
import os

path = os.path.join(os.path.dirname(__file__))
upload_path = os.path.join(path, "uploads")
files = []
for file in os.listdir(upload_path):
    if file.endswith(".pdf"):
        file_path = os.path.join(upload_path, file)
        files.append(file_path)

output_path = os.path.join(path, "output")
if not os.path.exists(output_path):
    os.makedirs(output_path)

result = subprocess.run(
    ["mineru", "-p", files[1], "-o", output_path, "-m", "txt", "-l", "en", "-d", "cuda", "--vram", "5"]
)
