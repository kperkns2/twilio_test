import requests
import json
import uuid
from tenacity import retry, stop_after_attempt, wait_fixed
import subprocess
import os
import shutil


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




def save_file_to_github(file_path):
  # Save the current working directory
  filename = os.path.basename(file_path)
  original_directory = os.getcwd()

  # Set your variables
  username = 'kperkns2'
  repository = 'twilio_test'
  email = 'kap20k4@gmail.com'
  git_token = 'your_git_personal_access_token_here'  # Make sure to replace this with your actual Git token

  # Configure git
  subprocess.run(['git', 'config', '--global', 'user.name', username], check=True)
  subprocess.run(['git', 'config', '--global', 'user.email', email], check=True)

  # Clone the repository
  clone_command = f'git clone https://github.com/{username}/{repository}.git'
  subprocess.run(clone_command, shell=True, check=True)

  # Change directory to the cloned repository
  os.chdir(f'./{repository}/')

  shutil.copy(file_path, os.getcwd())

  # Set the new origin with the token
  subprocess.run(['git', 'remote', 'rm', 'origin'], check=True)
  subprocess.run(['git', 'remote', 'add', 'origin', f'https://{git_token}@github.com/{username}/{repository}.git'], check=True)

  subprocess.run(['git', 'add', filename])
  subprocess.run(['git', 'commit', '-m', '"Added from streamlit"'])
  subprocess.run(['git', 'push', 'origin', 'main'])



  # Change back to the original directory
  os.chdir(original_directory)
