import json
import queue

import pyaudio
from vosk import KaldiRecognizer, Model

from config import VOSK_MODEL_PATH, AUDIO_RATE, AUDIO_CHANNELS


class SpeechListener:
    """Captures audio from USB microphone and converts speech to text using Vosk."""

    def __init__(self):
        self.model = Model(VOSK_MODEL_PATH)
        self.recognizer = KaldiRecognizer(self.model, AUDIO_RATE)
        self.audio = pyaudio.PyAudio()
        self._queue = queue.Queue()

    def _audio_callback(self, in_data, frame_count, time_info, status):
        self._queue.put(in_data)
        return (None, pyaudio.paContinue)

    def listen(self) -> str:
        """Listen for speech and return the transcribed text.

        Blocks until the user finishes speaking (Vosk detects a pause).
        Returns the recognized text, or an empty string if nothing was recognized.
        """
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=AUDIO_CHANNELS,
            rate=AUDIO_RATE,
            input=True,
            frames_per_buffer=4096,
            stream_callback=self._audio_callback,
        )
        stream.start_stream()

        print("Listening...")

        try:
            while True:
                data = self._queue.get()
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "")
                    if text:
                        return text
        except KeyboardInterrupt:
            return ""
        finally:
            stream.stop_stream()
            stream.close()
            # Clear any remaining audio in the queue
            while not self._queue.empty():
                self._queue.get_nowait()

    def close(self):
        self.audio.terminate()
