import subprocess
import tempfile
import wave

from config import PIPER_MODEL_PATH, PIPER_SPEAKER_ID


class PiperTTS:
    """Text-to-speech using Piper. Synthesises speech and plays it through the default audio output."""

    def __init__(self):
        self._check_piper_installed()

    def _check_piper_installed(self):
        """Verify that the piper binary is available."""
        try:
            subprocess.run(
                ["piper", "--help"],
                capture_output=True,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "Piper is not installed. Install it with: pip install piper-tts"
            )

    def speak(self, text: str):
        """Synthesise text to a WAV file with Piper, then play it via aplay."""
        if not text or not text.strip():
            return

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
            # Run piper to generate WAV
            piper_cmd = [
                "piper",
                "--model", PIPER_MODEL_PATH,
                "--output_file", tmp.name,
            ]
            if PIPER_SPEAKER_ID is not None:
                piper_cmd += ["--speaker", str(PIPER_SPEAKER_ID)]

            result = subprocess.run(
                piper_cmd,
                input=text,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                print(f"  [TTS error: {result.stderr.strip()}]")
                return

            # Play the generated audio through default output (USB speaker)
            subprocess.run(
                ["aplay", "-q", tmp.name],
                capture_output=True,
            )
