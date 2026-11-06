from fastapi import UploadFile

UPLOADS_DIR = "uploads"

def get_file_path(filename: str) -> str:
    return f"{UPLOADS_DIR}/{filename}"

def save_file(upload_file: UploadFile) -> None:
    path = get_file_path(upload_file.filename)
    with open(path, "wb") as buffer:
        buffer.write(upload_file.file.read())
    return path

def slugify(value: str) -> str:
    """
    Convert a string to a slug format.
    """
    import re
    value = value.lower()
    value = re.sub(r'[^a-z0-9]+', '-', value)
    value = re.sub(r'^-|-$', '', value)
    return value