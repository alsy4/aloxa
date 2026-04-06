"""Quick test: speak into the USB mic and see the transcription."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.speech.listener import SpeechListener


def main():
    listener = SpeechListener()
    print("Say something (Ctrl+C to stop)...")
    try:
        while True:
            text = listener.listen()
            print(f"You said: {text}")
    except KeyboardInterrupt:
        print("\nDone.")
    finally:
        listener.close()


if __name__ == "__main__":
    main()
