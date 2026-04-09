import difflib

import numpy as np
import pyaudio
from faster_whisper import WhisperModel

from config import WHISPER_MODEL, AUDIO_RATE, AUDIO_CHANNELS

# Silence threshold — frames below this RMS are considered silence
SILENCE_THRESHOLD = 500
# How many consecutive silent chunks before we stop recording
SILENCE_CHUNKS = 10
CHUNK_SIZE = 2048

# Fuzzy matching threshold (0.0–1.0); higher = stricter
_FUZZY_CUTOFF = 0.6


class SpeechListener:
    """Captures audio from USB microphone and converts speech to text using Whisper."""

    def __init__(self, medication_names: list[str] | None = None):
        print("  Loading Whisper model...")
        self.model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        self.audio = pyaudio.PyAudio()
        self.set_medication_names(medication_names or [])
        self._warm_up()

    def _warm_up(self):
        """Run a dummy transcription to warm up the model pipeline."""
        dummy = np.zeros(AUDIO_RATE, dtype=np.float32)
        segments, _ = self.model.transcribe(dummy, beam_size=1)
        for _ in segments:
            pass

    def set_medication_names(self, names: list[str]):
        """Update the list of known medication names used for prompting and fuzzy matching."""
        self._med_names = names
        self._initial_prompt = ", ".join(names) if names else None

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

        # Convert raw audio bytes to float32 numpy array for direct transcription
        raw = b"".join(frames)
        audio_array = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

        segments, _ = self.model.transcribe(
            audio_array,
            language="en",
            beam_size=1,
            initial_prompt=self._initial_prompt,
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        return self._fix_medication_names(text)

    def _fix_medication_names(self, text: str) -> str:
        """Replace words in text that fuzzy-match a known medication name."""
        if not self._med_names:
            return text

        words = text.split()
        fixed: list[str] = []
        i = 0
        while i < len(words):
            matched = False
            # Try matching multi-word medication names (longest first)
            for name in sorted(self._med_names, key=lambda n: -len(n.split())):
                n_words = len(name.split())
                candidate = " ".join(words[i:i + n_words])
                matches = difflib.get_close_matches(
                    candidate.lower(), [name.lower()], n=1, cutoff=_FUZZY_CUTOFF,
                )
                if matches:
                    fixed.append(name)
                    i += n_words
                    matched = True
                    break
            if not matched:
                fixed.append(words[i])
                i += 1
        return " ".join(fixed)

    def close(self):
        self.audio.terminate()
