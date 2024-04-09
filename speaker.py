import threading
from AudioTranscriber import AudioTranscriber
from GPTResponder import GPTSelenium
import customtkinter as ctk
import AudioRecorder 
import queue
import time
import torch
import sys
import TranscriberModels
import subprocess
import os
import argparse

os.environ['KMP_DUPLICATE_LIB_OK']='True'
f = None
def write_in_textbox(textbox, text):
    textbox.delete("0.0", "end")
    textbox.insert("0.0", text)

def update_transcript_UI(transcriber, textbox):
    transcript_string = transcriber.get_transcript()
    write_in_textbox(textbox, transcript_string)
    textbox.after(100, update_transcript_UI, transcriber, textbox)

def update_response_UI(responder, textbox):
    response = responder.response
    if len(response) > 0:
        reversed_array = response[::-1]
        result_string = '\n\n'.join(reversed_array)
        textbox.configure(state="normal")
        write_in_textbox(textbox, result_string)
        textbox.configure(state="disabled")

        textbox.after(300, update_response_UI, responder, textbox)

def clear_context(transcriber, audio_queue):
    transcriber.clear_transcript_data()
    with audio_queue.mutex:
        audio_queue.queue.clear()

def create_ui_components(root):
    # ctk.set_appearance_mode("dark")
    # ctk.set_default_color_theme("dark-blue")
    root.title("Speaker")
    
    # Hide title bar
    # root.overrideredirect(True)

    root.attributes("-alpha", 0.8)
   # Get screen width and height
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Calculate desired width and height based on screen size
    window_width = int(screen_width)
    window_height = int(0.5 * screen_height)
    # window_width = int(screen_width)
    # window_height = int(screen_height)

    # Set window geometry to fill the entire width and 30% of the height, and lock it at the bottom of the screen
    root.geometry(f"{window_width}x{window_height}+0+{screen_height - window_height}")


    font_size = 20

    transcript_textbox = ctk.CTkTextbox(root, width=screen_width/2, font=("Arial", font_size), text_color='#FFFCF2', wrap="word")
    transcript_textbox.grid(row=0, column=0, padx=10, pady=20, sticky="nsew")

    response_textbox = ctk.CTkTextbox(root, width=screen_width/2, font=("Arial", font_size), text_color='#639cdc', wrap="word")
    response_textbox.grid(row=0, column=1, padx=10, pady=20, sticky="nsew")

    # freeze_button = ctk.CTkButton(root, text="Freeze", command=None)
    # freeze_button.grid(row=2, column=0, padx=10, pady=3, sticky="nsew")

    # update_interval_slider_label = ctk.CTkLabel(root, text=f"", font=("Arial", 12), text_color="#FFFCF2")
    # update_interval_slider_label.grid(row=3, column=0, padx=10, pady=3, sticky="nsew")

    # update_interval_slider = ctk.CTkSlider(root, from_=1, to=10, width=300, height=20, number_of_steps=9)
    # update_interval_slider.set(2)
    # update_interval_slider.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")

    root.lift()
    root.attributes("-topmost", True)

    # return transcript_textbox, update_interval_slider, update_interval_slider_label, freeze_button
    return transcript_textbox, response_textbox

def main():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("ERROR: The ffmpeg library is not installed. Please install ffmpeg and try again.")
        return

    root = ctk.CTk()
    # transcript_textbox, update_interval_slider, update_interval_slider_label, freeze_button = create_ui_components(root)
    transcript_textbox, response_textbox = create_ui_components(root)

    audio_queue = queue.Queue()

    model = TranscriberModels.get_model('--api' in sys.argv)

    if '--file' in sys.argv:
        global f
        parser = argparse.ArgumentParser(description="Process a file (specify filename with --file argument).")
        parser.add_argument("--file", type=str, required=True, help="Path to the file to process.")
        args = parser.parse_args()
        f = open("conversation/" + args.file + ".txt", "a")
    speaker_audio_recorder = AudioRecorder.DefaultSpeakerRecorder()
    speaker_audio_recorder.record_into_queue(audio_queue)

    transcriber = AudioTranscriber(None, speaker_audio_recorder.source, model)
    responder = GPTSelenium()

    thread = threading.Thread(target=transcribe_thread, args=(audio_queue,transcript_textbox, transcriber, responder, response_textbox,))
    thread.daemon = True
    thread.start()
    # responder = GPTSelenium()
    # respond = threading.Thread(target=responder.respond_to_transcriber, args=(transcriber,))
    # respond.daemon = True
    # respond.start()

    print("READY")

    root.grid_rowconfigure(0, weight=100)
    root.grid_rowconfigure(1, weight=1)
    root.grid_rowconfigure(2, weight=1)
    root.grid_rowconfigure(3, weight=1)
    root.grid_columnconfigure(0, weight=2)
    root.grid_columnconfigure(1, weight=1)

    #  Add the clear transcript button to the UI
    # clear_transcript_button = ctk.CTkButton(root, text="Clear Transcript", command=lambda: clear_context(transcriber, audio_queue, ))
    # clear_transcript_button.grid(row=1, column=0, padx=10, pady=3, sticky="nsew")

 
    root.mainloop()

semaphore = threading.Semaphore(6)
last_spoken = None
import utils
def transcribe_thread(audio_queue, transcript_textbox, transcriber, responder, response_textbox):
    lenThread = threading.active_count()
    global f
    while True:
        who_spoke, data, time_spoken = audio_queue.get()
        transcribe = threading.Thread(target=transcriber.transcribe_audio_queue, args=(who_spoke, data, time_spoken,))
        transcribe.daemon = True
        transcribe.start()
        update_transcript_UI(transcriber, transcript_textbox)
        
        print("Active threads after starting new thread:", threading.active_count()-lenThread)
        cpu_usage = utils.check_cpu_usage()
        memory_usage = utils.check_cpu_usage()
        print(f"CPU Usage: {cpu_usage}%, Memory Usage: {memory_usage}%")

        speaker_response, gpt_response = None
        transcriber.respond_to_transcriber(transcriber, speaker_response, gpt_response)
        # gpt_thread = threading.Thread(target=transcriber.respond_to_transcriber, args=(transcriber, speaker_response, gpt_response,))
        # gpt_thread.daemon = True
        # gpt_thread.start()
        update_response_UI(responder, response_textbox)
        if f != None:
            if speaker_response != None: f.write(f"Speaker: {speaker_response}")
            if gpt_response != None: f.write(f"GPT Response: {gpt_response}")
        semaphore.release()


if __name__ == "__main__":
    main()