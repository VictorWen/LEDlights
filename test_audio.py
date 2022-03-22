import pyaudio
import wave
import sys
import time
import pafy
import ffmpeg

URL = "https://www.youtube.com/watch?v=ZavjGCQ95xI"

yt = pafy.new(URL)
audio_stream = yt.getbestaudio().url_https

node_input = ffmpeg.input(audio_stream)
node_output = node_input.output('pipe:', acodec="pcm_s16le", f="wav")
process = node_output.run_async(pipe_stdout=True)


with wave.open(process.stdout, 'rb') as wf:
    def callback(in_data, frame_count, time_info, status):
        data = wf.readframes(frame_count)
        return (data, pyaudio.paContinue)

    p = pyaudio.PyAudio()

    # open stream using callback (3)
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
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
    wf.close()

    # close PyAudio (7)
    p.terminate()
