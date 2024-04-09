import whisper
import torch
import wave
import os
import threading
import tempfile
import custom_speech_recognition as sr
import io
from datetime import timedelta
import pyaudio
from heapq import merge
from googletrans import Translator
import time
import utils
# Create a translator object
translator = Translator()

PHRASE_TIMEOUT = 12

MAX_PHRASES = 4

class AudioTranscriber:
    def __init__(self, mic_source, speaker_source, model):
        self.transcript_data = {"You": [], "Speaker": []}
        self.transcript_changed_event = threading.Event()
        self.audio_model = model
        self.active_threads = set()  # Set to track active threads
        self.last_spoken = None


        self.audio_sources = {
            "You": {},
            "Speaker": {}
        }

        if(mic_source != None):
            self.audio_sources['You'] = {
                "sample_rate": mic_source.SAMPLE_RATE,
                "sample_width": mic_source.SAMPLE_WIDTH,
                "channels": mic_source.channels,
                "last_sample": bytes(),
                "last_spoken": None,
                "new_phrase": True,
                "process_data_func": self.process_mic_data
            }

        if(speaker_source != None):
            self.audio_sources['Speaker'] = {
                "sample_rate": speaker_source.SAMPLE_RATE,
                "sample_width": speaker_source.SAMPLE_WIDTH,
                "channels": speaker_source.channels,
                "last_sample": bytes(),
                "last_spoken": None,
                "new_phrase": True,
                "process_data_func": self.process_speaker_data
            }
        
    def out_of_order_worker(self, who_spoke, data, time_spoken):
        self.update_last_sample_and_phrase_status(who_spoke, data, time_spoken)
        source_info = self.audio_sources[who_spoke]
        start_time = time.time()

        text = ''
        try:
            fd, path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            source_info["process_data_func"](source_info["last_sample"], path)
            result = self.audio_model.get_transcription(path)
            text = result['text'].strip()
            # print(text)
        except Exception as e:
            print(e)
        finally:
            os.unlink(path)

        if text != '' and text.lower() != 'you':
            translated_text = translator.translate(text, src='en', dest='vi')
            text += f"\n({translated_text.text})"
            end_time = time.time()
            duration = end_time - start_time
            # print("Duration:" + str(duration))
            self.update_transcript(who_spoke, text, time_spoken)
            self.transcript_changed_event.set()

        # Remove thread from active set after completion
        self.active_threads.remove(threading.current_thread())

    def transcribe_audio_queue_thread(self, audio_queue):
        while True:
            who_spoke, data, time_spoken = audio_queue.get()
            cpu_usage = utils.check_cpu_usage()
            memory_usage = utils.check_memory_usage()
            print(f"CPU Usage: {cpu_usage}%, Memory Usage: {memory_usage}%")
            if (cpu_usage > 80 or memory_usage > 90):
                for thread in self.active_threads:
                    thread.join()  # Wait for the thread to complete
                    if not thread.is_alive():
                        break  # Exit the inner loop after removing a finished thread

            if self.last_spoken == None:
                self.last_spoken = time_spoken

            if self.last_spoken <= time_spoken:
                self.last_spoken = time_spoken
                thread = threading.Thread(target=self.out_of_order_worker, args=(who_spoke, data, time_spoken))
                thread.daemon = True
                self.active_threads.add(thread)  # Add thread to active set
                thread.start()
                # ... (rest of the existing processing logic)

            # Check for active threads before exiting the loop
            if not self.active_threads:
                break  # Exit the loop if all threads are done

        # Main thread exits after processing out-of-order segments
    
    def transcribe_audio_queue(self, who_spoke, data, time_spoken):
            self.update_last_sample_and_phrase_status(who_spoke, data, time_spoken)
            source_info = self.audio_sources[who_spoke]
            start_time = time.time()

            text = ''
            try:
                fd, path = tempfile.mkstemp(suffix=".wav")
                os.close(fd)
                source_info["process_data_func"](source_info["last_sample"], path)
                result = self.audio_model.get_transcription(path)
                text = result['text'].strip()             
            except Exception as e:
                print(e)
            finally:
                os.unlink(path)

            if text != '' and text.lower() != 'you':
                translated_text = translator.translate(text, src='en', dest='vi')
                text += f"\n({translated_text.text})"
                print(text)
                end_time = time.time()
                duration = end_time - start_time
                print("Duration:" + str(duration))
                self.update_transcript(who_spoke, text, time_spoken)
                self.transcript_changed_event.set()


       

    def update_last_sample_and_phrase_status(self, who_spoke, data, time_spoken):
        source_info = self.audio_sources[who_spoke]
        if source_info["last_spoken"] and time_spoken - source_info["last_spoken"] >= timedelta(seconds=PHRASE_TIMEOUT):
            source_info["last_sample"] = bytes()
            source_info["last_spoken"] = None
            source_info["new_phrase"] = True
        else:
            source_info["new_phrase"] = False

        source_info["last_sample"] += data
        if source_info["last_spoken"] == None: 
            source_info["last_spoken"] = time_spoken 

    def process_mic_data(self, data, temp_file_name):
        audio_data = sr.AudioData(data, self.audio_sources["You"]["sample_rate"], self.audio_sources["You"]["sample_width"])
        wav_data = io.BytesIO(audio_data.get_wav_data())
        with open(temp_file_name, 'w+b') as f:
            f.write(wav_data.read())

    def process_speaker_data(self, data, temp_file_name):
        with wave.open(temp_file_name, 'wb') as wf:
            wf.setnchannels(self.audio_sources["Speaker"]["channels"])
            p = pyaudio.PyAudio()
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.audio_sources["Speaker"]["sample_rate"])
            wf.writeframes(data)

    def update_transcript(self, who_spoke, text, time_spoken):
        source_info = self.audio_sources[who_spoke]
        transcript = self.transcript_data[who_spoke]
        if source_info["new_phrase"] or len(transcript) == 0:
            if len(transcript) > MAX_PHRASES:
                transcript.pop(-1)
            transcript.insert(0, (f"{text}\n\n", time_spoken))
        else:
            transcript[0] = (f"{text}\n\n", time_spoken)

    def get_transcript(self):
        combined_transcript = list(merge(
            self.transcript_data["You"], self.transcript_data["Speaker"], 
            key=lambda x: x[1], reverse=True))
        return "".join([t[0] for t in combined_transcript])

    def is_new_phase(self, who_spoke):
        return self.audio_sources[who_spoke]["new_phrase"]
    
    def clear_transcript_data(self):
        self.transcript_data["You"].clear()
        self.transcript_data["Speaker"].clear()

        self.audio_sources["You"]["last_sample"] = bytes()
        self.audio_sources["Speaker"]["last_sample"] = bytes()

        self.audio_sources["You"]["new_phrase"] = True
        self.audio_sources["Speaker"]["new_phrase"] = True