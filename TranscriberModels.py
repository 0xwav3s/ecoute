import openai
import whisper
import os
import torch
import numpy as np

model_size = "large-v3"
import io

def get_model(use_api):
    if use_api:
        return APIWhisperTranscriber()
    else:
        return WhisperTranscriber()

class WhisperTranscriber:
    def __init__(self):
        self.audio_model = whisper.load_model(os.path.join(os.getcwd(), 'tiny.en.pt'))
        print(f"[INFO] Whisper using GPU: " + str(torch.cuda.is_available()))

    def get_transcription(self, wav_file_path):
        result = ''
        try:
            result = self.audio_model.transcribe(wav_file_path, fp16=torch.cuda.is_available())
        except Exception as e:
            print(e)
        return result
    
    def get_transcription_audio_data(self, audio_data):
        """Transcribes audio data in memory."""

        try:
            # Wrap the audio data in a BytesIO object if necessary
            # if isinstance(audio_data, io.BytesIO):
                # audio_data = np.frombuffer(audio_data.read(), dtype=np.int16)  # Assuming 16-bit audio
            with open("audio.mp3", "rb") as audio_file:
            # audio_bytes = audio_data.read()
                audio_file = io.BytesIO(audio_data)
                result = self.audio_model.transcribe(audio_file, fp16=torch.cuda.is_available())
                
            return result

        except Exception as e:
            print(f"Error during transcription: {e}")
            return None  # Return a more informative value on error
    
class APIWhisperTranscriber:
    def get_transcription(self, wav_file_path):
        try:
            with open(wav_file_path, "rb") as audio_file:
                result = openai.Audio.transcribe("whisper-1", audio_file)
        except Exception as e:
            print(e)
            return ''
        # return result['text'].strip()
        return result
    