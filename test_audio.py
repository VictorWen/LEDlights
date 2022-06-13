from io import BytesIO
import requests
import pyaudio
import time

resp = requests.get("http://victorwen-raspberrypi4:3000/stream", stream=True)
audio_stream = resp.raw

def callback(in_data, frame_count, time_info, status):
    data = audio_stream.read(frame_count * 8)
    return (data, pyaudio.paContinue)

p = pyaudio.PyAudio()


# open stream using callback (3)
stream = p.open(format=pyaudio.paInt32,
                frames_per_buffer=1024,
                channels=2,
                rate=44100,
                output=True,
                stream_callback=callback)

# start the stream (4)
stream.start_stream()

# wait for stream to finish (5)
while stream.is_active():
    time.sleep(0.1)

# stop stream (6)
stream.stop_stream()
stream.close()

# close PyAudio (7)
p.terminate()