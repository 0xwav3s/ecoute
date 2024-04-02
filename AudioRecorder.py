import custom_speech_recognition as sr
import pyaudio
from datetime import datetime
import utils

RECORD_TIMEOUT = 3
ENERGY_THRESHOLD = 1000
DYNAMIC_ENERGY_THRESHOLD = False

class BaseRecorder:
    def __init__(self, source, source_name):
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = ENERGY_THRESHOLD
        self.recorder.dynamic_energy_threshold = DYNAMIC_ENERGY_THRESHOLD

        if source is None:
            raise ValueError("audio source can't be None")

        self.source = source
        self.source_name = source_name

    def adjust_for_noise(self, device_name, msg):
        print(f"[INFO] Adjusting for ambient noise from {device_name}. " + msg)
        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)
        print(f"[INFO] Completed ambient noise adjustment for {device_name}.")

    def record_into_queue(self, audio_queue):
        def record_callback(_, audio:sr.AudioData) -> None:
            data = audio.get_raw_data()
            audio_queue.put((self.source_name, data, datetime.utcnow()))

        self.recorder.listen_in_background(self.source, record_callback, phrase_time_limit=RECORD_TIMEOUT)

class DefaultMicRecorder(BaseRecorder):
    def __init__(self):
        indexDefaultDevice = utils.getIndexMicrophoneDeviceDefault()
        p = pyaudio.PyAudio()
        default_speakers = p.get_device_info_by_index(indexDefaultDevice)
        
        source = sr.Microphone(speaker=True,
                               device_index= default_speakers["index"],
                               sample_rate=int(default_speakers["defaultSampleRate"]),
                               chunk_size=pyaudio.get_sample_size(pyaudio.paInt16),
                               channels=default_speakers["maxInputChannels"])

        super().__init__(source=source, source_name="You")

        self.adjust_for_noise("Default Mic", "Please make some noise from the Default Mic...")

class DefaultSpeakerRecorder(BaseRecorder):
    def __init__(self):
        indexDefaultDevice = utils.getIndexSpeakerDeviceDefault()
        p = pyaudio.PyAudio()
        default_speakers = p.get_device_info_by_index(indexDefaultDevice)
        source = sr.Microphone(speaker=True,
                               device_index= default_speakers["index"],
                               sample_rate=int(default_speakers["defaultSampleRate"]),
                               chunk_size=pyaudio.get_sample_size(pyaudio.paInt16),
                               channels=default_speakers["maxOutputChannels"])

        # source=sr.Microphone(speaker=True)
        super().__init__(source=source, source_name="Speaker")

        self.adjust_for_noise(default_speakers["name"], "Please make or play some noise from the Default Speaker...")