import tempfile
import wave

import numpy as np
import pyaudio
from faster_whisper import WhisperModel

from config import WHISPER_MODEL, AUDIO_RATE, AUDIO_CHANNELS

# Silence threshold — frames below this RMS are considered silence
SILENCE_THRESHOLD = 500
# How many consecutive silent chunks before we stop recording
SILENCE_CHUNKS = 30
CHUNK_SIZE = 1024


class SpeechListener:
    """Captures audio from USB microphone and converts speech to text using Whisper."""

    def __init__(self):
        print("  Loading Whisper model...")
        self.model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        self.audio = pyaudio.PyAudio()

    def listen(self) -> str:
        """Listen for speech and return the transcribed text.

        Records until silence is detected after speech, then transcribes.
        Returns the recognized text, or an empty string if nothing was recognized.
        """
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=AUDIO_CHANNELS,
            rate=AUDIO_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
        )

        print("  Listening...")

        frames = []
        silent_chunks = 0
        has_speech = False

        try:
            while True:
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))

                if rms > SILENCE_THRESHOLD:
                    has_speech = True
                    silent_chunks = 0
                    frames.append(data)
                elif has_speech:
                    silent_chunks += 1
                    frames.append(data)
                    if silent_chunks >= SILENCE_CHUNKS:
                        break
        except KeyboardInterrupt:
            return ""
        finally:
            stream.stop_stream()
            stream.close()

        if not frames:
            return ""

        # Write to a temp WAV file for Whisper
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
            with wave.open(tmp.name, "wb") as wf:
                wf.setnchannels(AUDIO_CHANNELS)
                wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(AUDIO_RATE)
                wf.writeframes(b"".join(frames))

            segments, _ = self.model.transcribe(tmp.name, language="en")
            return " ".join(seg.text.strip() for seg in segments).strip()

    def close(self):
        self.audio.terminate()
