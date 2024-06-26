from utils import *

import streamlit as st
import random

# Authenticate and set up
authenticate_google()
token_dictionary = get_token_dictionary()

# A list to hold dictionaries of text and speaker tokens
if 'text_speaker_pairs' not in st.session_state:
    st.session_state['text_speaker_pairs'] = []
if 'audio_filenames' not in st.session_state:
    st.session_state['audio_filenames'] = []


def add_to_list():
    """Adds the current text and speaker token to the list."""
    st.session_state['text_speaker_pairs'].append({
        "text": text_to_speak,
        "speaker_token": speaker_token
    })

    filename = f"output_{str.zfill(str(random.randint(0,1000000000)),10)}.wav"

    inference_job_token = make_initial_request(tts_model_token=speaker_token, inference_text=text_to_speak)
    if inference_job_token:
        download_wav_if_complete(inference_job_token, filename)
        st.audio(filename)

        bucket_id = st.secrets["bucket"]["id"]
        upload_file_to_gcs(filename, bucket_id, filename)

        st.session_state['audio_filenames'].append(filename)



def on_click_send_message():
    """Processes the current text and speaker, uploads the result, and possibly initiates a call."""
    st.write("Processing...")
    initiate_call(target_phone_number=phone_number, url_list=st.session_state['audio_filenames'])

# Streamlit UI Components
st.title("Text to Speech & Twilio")

name = st.selectbox("Choose a speaker", list(token_dictionary.keys()))
speaker_token = token_dictionary[name]


text_to_speak = st.text_input("Text to speak",
                              value='How much wood could a woodchuck chuck if a woodchuck could chuck wood?')
st.button("Add to List", on_click=add_to_list)

st.divider()

phone_number = st.text_input("Phone number to call", value='2174807363')
st.button("Click to send message!", on_click=on_click_send_message)




# Define the chatgpt_complete function as a placeholder. This should be replaced with actual API call.
def chatgpt_complete(text_speaker_pairs):
    # This is a placeholder for the function that calls the OpenAI API to generate text.
    # Replace this with actual code to call the API and use `text_speaker_pairs` as input.
    return "This is a generated narrator script filling the gaps. (Replace this with actual API response.)"