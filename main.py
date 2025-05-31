# transcribe.py
import sys
from faster_whisper import WhisperModel

if len(sys.argv) < 2:
    print("Usage: python transcribe.py <audio_file>")
    sys.exit(1)

audio_path = sys.argv[1]

model = WhisperModel("large-v3", device="cuda", compute_type="float16")
segments, info = model.transcribe(audio_path, beam_size=5)

print(f"Detected language: {info.language}")
print("\nTranscription:\n")

for segment in segments:
    print(segment.text)
