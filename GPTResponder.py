import openai
from keys import OPENAI_API_KEY
from prompts import create_prompt, create_question_suggest, INITIAL_RESPONSE
import time
import re

from AudioTranscriber import MAX_PHRASES
openai.api_key = OPENAI_API_KEY
import os
from GPT.pyChatGPT import ChatGPT
from dotenv import dotenv_values
from googletrans import Translator
translator = Translator()
keywords = [
    "what", "how", "why", "when", "where", "who", "which", "whose", "whom",
    "do", "does", "did", "is", "are", "was", "were", "can", "could", "will", "would"
]
def generate_response_from_transcript(transcript):
    try:
        response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0301",
                messages=[{"role": "system", "content": create_prompt(transcript)}],
                temperature = 0.0
        )
    except Exception as e:
        print(e)
        return ''
    full_response = response.choices[0].message.content
    try:
        return full_response.split('[')[1].split(']')[0]
    except:
        return ''
    
class GPTResponder:
    def __init__(self):
        self.response = INITIAL_RESPONSE
        self.response_interval = 2

    def respond_to_transcriber(self, transcriber):
        while True:
            if transcriber.transcript_changed_event.is_set():
                start_time = time.time()

                transcriber.transcript_changed_event.clear() 
                transcript_string = transcriber.get_transcript()
                # response = generate_response_from_transcript(transcript_string)
                response = transcript_string
                # print(response)
                end_time = time.time()  # Measure end time
                execution_time = end_time - start_time  # Calculate the time it took to execute the function
                
                if response != '':
                    self.response = response

                remaining_time = self.response_interval - execution_time
                if remaining_time > 0:
                    time.sleep(remaining_time)
            else:
                time.sleep(0.3)

    def update_response_interval(self, interval):
        self.response_interval = interval

class GPTSelenium:
    def __init__(self):
        env_vars = dotenv_values(".env")
        current_directory = os.getcwd()
        email = env_vars['EMAIL']
        password = env_vars['PASSWORD']
        conversation_id = env_vars['CONVERSATION_ID']

        self.gpt_improve = ChatGPT(auth_type='openai', 
              email=email, 
              password=password, 
              conversation_id=conversation_id,
              login_cookies_path=current_directory+'/cookies',
              )
        self.response = [INITIAL_RESPONSE]
        self.questions = []

    def getResponse(self, transcript):
        resp = self.gpt_improve.send_message(transcript)
        return resp['message']
    
    def respond_to_transcriber(self, transcriber):
        # while True:
            is_new_phase = transcriber.is_new_phase('Speaker')
            speaker_response = None
            gpt_response = None
            transcript_string = ''.join(map(str, transcriber.get_transcript()))
            pattern = r"[a-zA-Z0-9]+"
            match = re.search(pattern, transcript_string)
            if is_new_phase and match:
                speaker_response = transcript_string
                start_time = time.time()
                response = ''
                question_contains_keyword = any(keyword in transcript_string.lower() for keyword in keywords) if transcript_string.lower() else False
                first_question = transcript_string.split('\n')[0]
                if question_contains_keyword:
                    # if first_question != None and is_new_phase and first_question not in self.response:
                    if first_question not in self.questions:
                        self.questions.append(first_question)
                        response = self.getResponse(create_question_suggest(first_question))
                        translated_text = translator.translate(response, src='en', dest='vi')
                        response += f"\n({translated_text.text})"
                        gpt_response = response
                    # print(response)
                    end_time = time.time()  # Measure end time
                    execution_time = end_time - start_time  # Calculate the time it took to execute the function
                    print("Duration GPT Response: " + str(execution_time) + "s")
                if response != '':
                    self.response.append(response)
                if len(self.response) > MAX_PHRASES:
                    self.response = []
                    self.questions = []
            return speaker_response, gpt_response

