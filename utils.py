import pyaudio
import psutil  
import re
p = pyaudio.PyAudio()
keywords = [
    "what", "how", "why", "when", "where", "who", "which", "whose", "whom",
    "do", "does", "did", "is", "are", "was", "were", "can", "could", "will", "would"
]
def getIndexSpeakerDeviceDefault():
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if device_info["maxOutputChannels"] > 0:
            nameDevice = device_info["name"]
            for item in ["BlackHole"]:
                # print(nameDevice + ":" + item)
                if(item in nameDevice):
                    print("[INFO] Use this device: " + nameDevice)
                    return device_info["index"]
    return None

def getIndexMicrophoneDeviceDefault():
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if device_info["maxOutputChannels"] == 0:
            nameDevice = device_info["name"]
            for item in ["Microphone"]:
                # print(nameDevice + ":" + item)
                if(item in nameDevice):
                    print("[INFO] Use this device: " + nameDevice)
                    return device_info["index"]
    return None

def check_cpu_usage():    
    return psutil.cpu_percent()

def check_memory_usage():
    return psutil.virtual_memory().percent

def is_question(text):
    """Check if a string represents a question using regular expressions."""
    if isinstance(text, str):
        # Define a regular expression pattern to match a question
        question_pattern = rf'\b({"|".join(keywords)})\b|\?'
        # Use re.search() to see if the text matches the pattern
        if re.search(question_pattern, text.lower()):
            return True
    return False
