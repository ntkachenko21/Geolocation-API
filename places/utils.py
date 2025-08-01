import os
import uuid


def place_photo_path(_, filename):
    """Function to create a unique photo path"""
    ext = filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("places", "photos", filename)
