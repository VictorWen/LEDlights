from datetime import datetime
from gc import callbacks
from effects import BaseEffect, DYNAMIC, STATIC
import wave
import pyaudio
import math
import asyncio

class AudioPlayer:
    def write(self, bytes):
        pass

    def setup(self, width, channels, rate):
        pass

    def close(self):
        pass


class PyAudioPlayer:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.buffer = b''
        self.started = False

    def setup(self, width, channels, rate):
        self.width = width
        self.channels = channels
        self.stream = self.p.open(
            format=self.p.get_format_from_width(width),
            channels=channels,
            rate=rate,
            output=True,
            stream_callback= lambda in_data, frame_count, time_info, status : self.read(in_data, frame_count, time_info, status)
        )
    
    def write(self, bytes):
        if not self.started:
            self.stream.start_stream()
            self.started = True
        self.buffer += bytes
    
    def read(self, in_data, frame_count, time_info, status):
        N = frame_count * self.width * self.channels
        data = self.buffer[0:N]
        self.buffer = self.buffer[N::]

        return (data, pyaudio.paContinue)

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()


class PlayMusic(BaseEffect):
    def __init__(self, wavfile, playback=None):
        super().__init__(type=DYNAMIC)
        self.wavfile = wave.open(wavfile, 'rb')

        self.width = self.wavfile.getsampwidth()
        self.nchannels = self.wavfile.getnchannels()
        self.rate = self.wavfile.getframerate()

        self.nframes = self.wavfile.getnframes()
        self.time_sum = 0
        self.frame = 0

        if playback is None:
            self.playback = PyAudioPlayer()
        else:
            self.playback = playback

        self.playback.setup(
            width = self.width,
            channels = self.nchannels,
            rate = self.rate
        )

    def tick(self, pixels, time_delta):
        self.time_sum += time_delta
        read = min(int(self.time_sum * self.rate - self.frame), self.nframes - self.frame)
        if read == 0:
            print("CLOSED")
            self.wavfile.close()
            self.playback.close()
            self.type = STATIC
            return
        self.frame += read
        data = self.wavfile.readframes(read)
        self.playback.write(data)
