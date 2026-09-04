# backend/app/path_test.py

from pathlib import Path

dir1 = Path(__file__)
dir2 = Path(__file__).parent.parent.parent
dir3 = dir2 / ".env"
# print(f"Current file's diretory is {dir1}.")
# print(f"And its parent's parent's parent is {dir2}")
# print(f"The .env file's directory is {dir3}")
# print(dir3.read_text(encoding="utf-8"))

print(dir1)
