import pyaudio
p = pyaudio.PyAudio()
import psutil  
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