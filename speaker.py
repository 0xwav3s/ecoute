import threading
from AudioTranscriber import AudioTranscriber
from GPTResponder import GPTResponder
import customtkinter as ctk
import AudioRecorder 
import queue
import time
import torch
import sys
import TranscriberModels
import subprocess
import os

os.environ['KMP_DUPLICATE_LIB_OK']='True'

def write_in_textbox(textbox, text):
    textbox.delete("0.0", "end")
    textbox.insert("0.0", text)

def update_transcript_UI(transcriber, textbox):
    transcript_string = transcriber.get_transcript()
    write_in_textbox(textbox, transcript_string)
    textbox.after(100, update_transcript_UI, transcriber, textbox)

def update_response_UI(responder, textbox, update_interval_slider_label, update_interval_slider, freeze_state):
    if not freeze_state[0]:
        response = responder.response

        textbox.configure(state="normal")
        write_in_textbox(textbox, response)
        textbox.configure(state="disabled")

        update_interval = int(update_interval_slider.get())
        responder.update_response_interval(update_interval)
        update_interval_slider_label.configure(text=f"Update interval: {update_interval} seconds")

    textbox.after(300, update_response_UI, responder, textbox, update_interval_slider_label, update_interval_slider, freeze_state)

def clear_context(transcriber, audio_queue):
    transcriber.clear_transcript_data()
    with audio_queue.mutex:
        audio_queue.queue.clear()

def create_ui_components(root):
    # ctk.set_appearance_mode("dark")
    # ctk.set_default_color_theme("dark-blue")
    # root.title("Speaker")
    
    # Hide title bar
    root.overrideredirect(True)

    root.attributes("-alpha", 0.65)
   # Get screen width and height
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Calculate desired width and height based on screen size
    window_width = int(screen_width)
    window_height = int(0.3 * screen_height)

    # Set window geometry to fill the entire width and 30% of the height, and lock it at the bottom of the screen
    root.geometry(f"{window_width}x{window_height}+0+{screen_height - window_height}")


    font_size = 20

    transcript_textbox = ctk.CTkTextbox(root, width=window_width, font=("Arial", font_size), text_color='#FFFCF2', wrap="word")
    transcript_textbox.grid(row=0, column=0, padx=10, pady=20, sticky="nsew")

    # response_textbox = ctk.CTkTextbox(root, width=300, font=("Arial", font_size), text_color='#639cdc', wrap="word")
    # response_textbox.grid(row=0, column=1, padx=10, pady=20, sticky="nsew")

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
    return transcript_textbox

def main():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("ERROR: The ffmpeg library is not installed. Please install ffmpeg and try again.")
        return

    root = ctk.CTk()
    # transcript_textbox, update_interval_slider, update_interval_slider_label, freeze_button = create_ui_components(root)
    transcript_textbox = create_ui_components(root)

    audio_queue = queue.Queue()

    model = TranscriberModels.get_model('--api' in sys.argv)

    time.sleep(2)

    
    thread = threading.Thread(target=transcribe_thread, args=(audio_queue, model, transcript_textbox,))
    thread.daemon = True
    thread.start()
    # responder = GPTResponder()
    # respond = threading.Thread(target=responder.respond_to_transcriber, args=(transcriber,))
    # respond.daemon = True
    # respond.start()

    print("READY")

    root.grid_rowconfigure(0, weight=100)
    root.grid_rowconfigure(1, weight=1)
    root.grid_rowconfigure(2, weight=1)
    root.grid_rowconfigure(3, weight=1)
    root.grid_columnconfigure(0, weight=2)
    # root.grid_columnconfigure(1, weight=1)

    #  Add the clear transcript button to the UI
    # clear_transcript_button = ctk.CTkButton(root, text="Clear Transcript", command=lambda: clear_context(transcriber, audio_queue, ))
    # clear_transcript_button.grid(row=1, column=0, padx=10, pady=3, sticky="nsew")

 
    root.mainloop()

semaphore = threading.Semaphore(6)
import utils
def transcribe_thread(audio_queue, model, transcript_textbox):
    speaker_audio_recorder = AudioRecorder.DefaultSpeakerRecorder()
    speaker_audio_recorder.record_into_queue(audio_queue)
    transcriber = AudioTranscriber(None, speaker_audio_recorder.source, model)
    lenThread = threading.active_count()
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
        semaphore.release()


if __name__ == "__main__":
    main()