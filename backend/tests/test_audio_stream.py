import asyncio
import os
import sys

# Add parent dir
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from streams.audio import audio_stream

async def main():
    # Construct absolute path to the test file: ../test/fake_tts.wav relative to this script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    audio_path = os.path.join(base_dir, '..', 'test', 'fake_tts.wav')
    
    if not os.path.exists(audio_path):
        print(f"File not found: {audio_path}")
        return

    print(f"Testing audio file: {audio_path}")
    with open(audio_path, "rb") as f:
        file_bytes = f.read()

    result = await audio_stream.analyze(file_bytes)

    print("\n=== AUDIO DEEPFAKE RESULT ===")
    import json
    # Use json dump for pretty printing dict
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
