import requests
import json
import uuid
from tenacity import retry, stop_after_attempt, wait_fixed
import subprocess
import os
import shutil


import streamlit as st
import json
from google.oauth2 import service_account
from google.cloud import storage

def authenticate_google():
  # Load the service account key from Streamlit secrets
  gcp_service_account_info = json.loads(st.secrets["gcp_service_account"]["key"])

  # Authenticate with the service account
  credentials = service_account.Credentials.from_service_account_info(gcp_service_account_info)

  # Now you can use the credentials with Google Cloud Client Libraries
  # For example, initializing the storage client
  storage_client = storage.Client(credentials=credentials, project=credentials.project_id)
  return storage_client


def upload_file_to_gcs(file_path, bucket_name, destination_blob_name):
    """
    Uploads a file from the specified file path to a Google Cloud Storage bucket.

    :param file_path: Path to the file to upload.
    :param bucket_name: ID of the GCS bucket.
    :param destination_blob_name: The desired name of the file in the bucket.
    """
    # Assuming you already have an authenticated storage client
    storage_client = authenticate_google()

    # Get the bucket
    bucket = storage_client.bucket(bucket_name)
    
    # Create a new blob and upload the file's content from the file path
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(file_path)
    
    # Assuming you'd like to print or return the public URL (if the file is publicly accessible)
    # Note: Make sure the file is publicly accessible if you need a public URL.
    # blob.make_public() # Uncomment if the blob should be made public.
    print(f"File {file_path} uploaded to {destination_blob_name}. Public URL: {blob.public_url}")




def get_token_dictionary():
  tts_list = requests.get("https://api.fakeyou.com/tts/list")
  tts_list = tts_list.json()
  all_titles = [t['title'] for t in tts_list['models']]

  # Mapping of human-readable names to full titles
  title_mapping = json.load(open("title_mapping.json","r"))

  # Creating a dictionary with specified titles as keys
  token_dictionary = {name: next((t['model_token'] for t in tts_list['models'] 
    if t['title'] == title), None) for name, title in title_mapping.items()}
  return token_dictionary


def generate_random_uuid():
    # Generate a random UUID and return it
    return str(uuid.uuid4())


def make_initial_request(tts_model_token="TM:7wbtjphx8h8v", inference_text="Hello world! My name is Mario."):
    url = 'https://api.fakeyou.com/tts/inference'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    random_uuid = generate_random_uuid()
    data = {
        "uuid_idempotency_token": str(random_uuid),
        "tts_model_token": tts_model_token,
        "inference_text": inference_text
    }
    response = requests.post(url, headers=headers, json=data)

    response_data = response.json()
    if response_data.get("success") == True:
        return response_data.get("inference_job_token")
    else:
        print("Error in initial request:", response_data.get("error_reason",''))
        return None


def fetch_job_result(inference_job_token):
    if not inference_job_token:
        print("Invalid or missing inference job token.")
        return

    url = f'https://api.fakeyou.com/tts/job/{inference_job_token}'
    headers = {
        'Accept': 'application/json'
    }
    response = requests.get(url, headers=headers)
    response_data = response.json()

    # Pretty print the JSON response or handle it as needed
    print(response_data)
    return response_data

@retry(stop=stop_after_attempt(15), wait=wait_fixed(3))
def download_wav_if_complete(inference_job_token):
    job_result = fetch_job_result(inference_job_token)
    # Check if the job completed successfully
    if job_result.get('success') and job_result['state']['status'] == 'complete_success':
        # Construct the URL to the WAV file
        base_url = 'https://storage.googleapis.com/vocodes-public'
        wav_path = job_result['state']['maybe_public_bucket_wav_audio_path']
        wav_url = f'{base_url}{wav_path}'

        # Attempt to download the WAV file
        response = requests.get(wav_url)
        if response.status_code == 200:
            # Define where you want to save the WAV file, e.g., "output.wav"
            file_path = 'output.wav'
            with open(file_path, 'wb') as file:
                file.write(response.content)
            print(f'File successfully downloaded to {file_path}')
        else:
            # Print detailed error information
            print(f'Failed to download the WAV file. HTTP Status Code: {response.status_code}')
            try:
                # Attempt to parse and print any JSON error message
                error_details = response.json()
                print(f'Error Details: {error_details}')
            except ValueError:
                # Fallback if the response isn't JSON-formatted
                print(f'Response: {response.text}')
    else:
        raise Exception("Job not completed yet")
        print('Job is not in complete_success state.')
