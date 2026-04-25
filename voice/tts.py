import re
import subprocess
import tempfile
import wave

from config import PIPER_MODEL_PATH, PIPER_SPEAKER_ID


# Replacements that turn typographic punctuation into speech-friendly forms.
_SPEECH_SUBSTITUTIONS = [
    (re.compile(r"\s*[—–]\s*"), ", "),     # em / en dash → comma pause
    (re.compile(r"…"), "."),                # ellipsis → period
    (re.compile(r"\s*[•·]\s*"), ", "),      # bullets → comma pause
    (re.compile(r"\s*&\s*"), " and "),
]

# Markdown / structural symbols Piper would otherwise read aloud literally.
# Natural-prosody punctuation (. , ; : ! ? ( ) ' ") is intentionally kept.
_STRIP_SYMBOLS_RE = re.compile(r"[*_~`#\[\]{}<>|\\^=+]")

# Defensive emoji / pictograph strip (the system prompts forbid emoji, but
# we don't want Piper to ever spell out a stray symbol).
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "]+",
    flags=re.UNICODE,
)

_WHITESPACE_RE = re.compile(r"\s+")


def sanitize_for_speech(text: str) -> str:
    """Strip / replace characters Piper would mispronounce or read literally."""
    if not text:
        return text
    for pattern, repl in _SPEECH_SUBSTITUTIONS:
        text = pattern.sub(repl, text)
    text = _EMOJI_RE.sub("", text)
    text = _STRIP_SYMBOLS_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    # Tidy up any " ," or " ." artefacts left after stripping.
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text


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

        text = sanitize_for_speech(text)
        if not text:
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
