import os
import requests
from google.cloud import storage
from utils.config import *

def download_file(url: str, filename: str):
    headers = {
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }
    try:
        # Read the response in chunks to avoid memory issues
        with requests.get(url, headers=headers, stream=True) as response:
            # Covert HTTP error to exceptions to catch them
            response.raise_for_status()  
            with open(filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  
                        f.write(chunk)
        print(f"File downloaded successfully: {filename}")
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"
    
def upload_file(file_name):
    # Connect to the bucket
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # Define the blob (an object in the bucket)
    blob = bucket.blob(file_name)
    blob.upload_from_filename(file_name)

    print(f"File uploaded successfully: {file_name}")


def remove_local_file(file_name):
    if os.path.exists(file_name):
        os.remove(file_name)
        print(f"Local file removed: {file_name}")
    else:
        print(f"Local file not found: {file_name}")