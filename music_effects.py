from effects import BaseEffect, DYNAMIC, STATIC
import wave
import pyaudio
import subprocess
import numpy as np
from numpy.fft import rfft, rfftfreq
from scipy.fftpack import next_fast_len
from color_utils import *
import math
import time


def bin_frequencies(ints, freqs, nbins, min_freq, max_freq, linear=True):
    if linear:
        portion = (max_freq - min_freq) / nbins
        next_max = min_freq + portion
    else:
        portion = (max_freq / min_freq) ** (1 / nbins)
        next_max = min_freq * portion
    
    # print(next_max)

    # print(ints, freqs)

    N = len(ints)
    bins = [ 0 for i in range(nbins)]
    bin_index = 0

    bin = 0
    bin_size = 0
    for i in range(N):
        if freqs[i] < min_freq:
            continue
        while freqs[i] >= next_max:
            # if bin_size > 0:
                # bin /= bin_size
            
            bins[bin_index] = bin
            bin_index += 1
            bin = 0
            bin_size = 0

            if linear:
                next_max += portion
            else:
                next_max *= portion
            # print(next_max)
            if next_max > max_freq:
                return np.array(bins)
        
        if freqs[i] < next_max:
            bin += ints[i]
            bin_size += 1
    
    
    return np.array(bins)


class AudioPlayer:
    def write(self, bytes):
        pass

    def setup(self, width, channels, rate):
        pass

    def close(self):
        pass


class PyAudioPlayer:
    def setup(self, width, channels, rate):
        self.min_buffer_size = 10000
        self.max_buffer_size = 50000

        self.buffer = b''
        self.started = False
        self.p = pyaudio.PyAudio()
        subprocess.call(["amixer", "sset", "Headphone", "85%"])

        self.width = width
        self.channels = channels
        self.stream = self.p.open(
            format=self.p.get_format_from_width(width),
            channels=channels,
            rate=rate,
            output=True,
            stream_callback= lambda in_data, frame_count, time_info, status : self.read(in_data, frame_count, time_info, status),
            start=False
        )

    def write(self, bytes):
        if (len(self.buffer) + len(bytes)) > self.max_buffer_size:
            return 
        self.buffer += bytes
        if not self.started and len(self.buffer) >= self.min_buffer_size:
            self.stream.start_stream()
            self.started = True
    
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
        self.wavfile = wavfile

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
        if (time_delta > 1):
            return
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


class SpectrumEffect(BaseEffect):
    def __init__(self, color, wavfile, playback=None, linear=True, nbins=37, min_freq=115, max_freq=900):
        super().__init__(type=DYNAMIC)
        self.wavfile = wavfile
        self.color = color

        self.width = self.wavfile.getsampwidth()
        self.nchannels = self.wavfile.getnchannels()
        self.rate = self.wavfile.getframerate()

        self.nframes = self.wavfile.getnframes()
        self.time_sum = 0
        self.frame = 0

        self.threshold = 1E7
        self.nbins = nbins
        self.min_freq = min_freq
        self.max_freq = max_freq
        self.linear = linear

        self.closed = False

        self.playback = playback
        if self.playback is not None:
            self.playback.setup(
                width = self.width,
                channels = self.nchannels,
                rate = self.rate
            )
    
    def tick(self, pixels, time_delta):
        if (time_delta > 1):
            return
        self.time_sum += time_delta
        read = min(int(self.time_sum * self.rate - self.frame), self.nframes - self.frame)
        if read == 0 and not self.closed:
            self.wavfile.close()
            if self.playback is not None:
                self.playback.close()
            self.type = STATIC
            return
        self.frame += read
        
        data = self.wavfile.readframes(read)
        if self.playback is not None:
            self.playback.write(data)

        values = np.frombuffer(data, dtype="<i2")
        length = next_fast_len(read)

        ints = rfft(values, length)
        ints = abs(ints)

        freq = rfftfreq(length, 1/self.rate)

        bins = bin_frequencies(ints, freq, self.nbins, self.min_freq, self.max_freq, linear=self.linear)
        bin_max = bins.max()

        self.threshold = max((2 - time_delta) / 2, 0) * self.threshold + min(time_delta / 2, 1) * bin_max * 1

        # bins = np.log10((bins + 1) / self.threshold * 10)
        bins = (np.power(100, (bins / self.threshold)) - 1) / 99
        # bins = np.log10(9 * bins / self.threshold + 1)
        # bins = bins / self.threshold
        
        for i in range(len(bins)):
            bin = bins[i]
            if bin > 1:
                bin = 1
            elif bin < 0.1:
                bin = 0
            bins[i] = bin
        
        # print(bins)

        color = clone_pixels(pixels)
        self.color.tick(color, time_delta)
        N = len(color)

        for i in range(N):
            index = int(i / N * (self.nbins - 1))
            pixels[i] = color[int(bins[index] * (N - 1))]

