import os

def find_non_utf8_files(directory):
    for folder, _, files in os.walk(directory):
        for name in files:
            if name.endswith(".py"):
                path = os.path.join(folder, name)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        f.read()
                except UnicodeDecodeError:
                    print(f"❌ Not UTF-8: {path}")

find_non_utf8_files(".")