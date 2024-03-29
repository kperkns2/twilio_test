from utils import *

import streamlit as st

token_dictionary = get_token_dictionary()

def on_click():
  st.write("Processing...")
  inference_job_token = make_initial_request(tts_model_token=speaker_token,
                                            inference_text=text_to_speak)
  if inference_job_token:
    st.write(download_wav_if_complete(inference_job_token))
    
    

st.button("Click me!", on_click=on_click)

st.write('Hello World!')

name = st.selectbox("Choose a speaker", list(token_dictionary.keys()))
speaker_token = token_dictionary[name]

text_to_speak = st.text_input("Text to speak", placeholder='How much wood could a woodchuck chuck if a woodchuck could chuck wood?')


