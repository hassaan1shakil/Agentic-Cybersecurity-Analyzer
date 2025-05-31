import signal
import wave
import numpy as np
import pyaudio
import scipy.signal
from faster_whisper import WhisperModel

# Audio recording parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
INPUT_RATE = 44100  # Mic input rate
TARGET_RATE = 16000  # Whisper expects 16kHz
CHUNK = 1024
RECORD_SECONDS = 10

# Load Whisper model
model = WhisperModel("large-v3", device="cuda", compute_type="float16")

# Initialize PyAudio
p = pyaudio.PyAudio()
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=INPUT_RATE,
    input=True,
    frames_per_buffer=CHUNK,
)

print("Recording from microphone. Press Ctrl+C to stop...")

stop_flag = False


def signal_handler(sig, frame):
    global stop_flag
    stop_flag = True
    print("\nStopping...")


signal.signal(signal.SIGINT, signal_handler)


def write_wave_file(filename, audio_data, sample_rate):
    wf = wave.open(filename, "wb")
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(sample_rate)
    wf.writeframes(audio_data)
    wf.close()


def resample_audio(audio_bytes, input_rate, output_rate):
    audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
    num_samples = int(len(audio_np) * output_rate / input_rate)
    resampled = scipy.signal.resample(audio_np, num_samples)
    return resampled.astype(np.int16).tobytes()


output_file = "output.txt"
with open(output_file, "w", encoding="utf-8") as out_f:
    try:
        while not stop_flag:
            frames = []
            for _ in range(0, int(INPUT_RATE / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)

            raw_audio = b"".join(frames)
            resampled_audio = resample_audio(
                raw_audio, INPUT_RATE, TARGET_RATE)

            temp_filename = "temp_chunk.wav"
            write_wave_file(temp_filename, resampled_audio, TARGET_RATE)

            segments, info = model.transcribe(
                temp_filename, language="ur", beam_size=5)
            print(f"\n[Detected language: {info.language}]")
            for segment in segments:
                print(segment.text)
                out_f.write(segment.text + "\n")
            out_f.flush()

    except KeyboardInterrupt:
        stop_flag = True

# Cleanup
stream.stop_stream()
stream.close()
p.terminate()
print(f"Transcription saved to {output_file}")
