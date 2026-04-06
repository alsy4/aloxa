"""Test audio transcription using the Vosk speech listener."""

from src.speech.listener import SpeechListener


def main():
    listener = SpeechListener()
    print("Speak into the mic (Ctrl+C to stop)...\n")
    try:
        while True:
            text = listener.listen()
            if text:
                print(f"  Transcribed: {text}")
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        listener.close()


if __name__ == "__main__":
    main()
