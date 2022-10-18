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
    bins = [0 for i in range(nbins)]
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


def fft(values, length, rate, nbins, min_freq, max_freq, linear, time_delta, threshold, fade):
    length = next_fast_len(length)

    ints = rfft(values, length)
    ints = abs(ints)

    freq = rfftfreq(length, 1/rate)

    bins = bin_frequencies(ints, freq, nbins, min_freq,
                           max_freq, linear=linear)
    bin_max = bins.max()

    threshold = max((2 - time_delta) / 2, 0) * threshold + \
        min(time_delta / 2, 1) * bin_max * 0.80

    # bins = np.log10((bins + 1) / self.threshold * 10)
    bins = (np.power(100, (bins / threshold)) - 1) / 99
    # bins = np.log10(9 * bins / self.threshold + 1)
    # bins = bins / self.threshold

    for i in range(len(bins)):
        bin = bins[i] + fade[i]
        if bin > 1:
            bin = 1
        elif bin < 0.1:
            bin = 0
        bins[i] = bin
        fade[i] = bins[i] * 0.75

    return bins, threshold


def fill_pixels_from_bins(bins, nbins, pixels, N, color):
    for i in range(N):
        index = int(i / N * (nbins - 1))
        pixels[i] = color[int(bins[index] * (N - 1))]


class AudioPlayer:
    def write(self, bytes):
        pass

    def setup(self, width, channels, rate):
        pass

    def close(self):
        pass


class PyAudioPlayer:
    def setup(self, width, channels, rate, format_override=None):
        self.min_buffer_size = rate * width * channels / 5
        self.max_buffer_size = self.min_buffer_size * 2
        print(self.min_buffer_size, self.max_buffer_size)

        self.buffer = b''
        self.started = False
        self.p = pyaudio.PyAudio()
        # subprocess.call(["amixer", "sset", "Headphone", "85%"])

        self.width = width
        self.channels = channels

        format = format_override
        if format_override is None:
            format = self.p.get_format_from_width(width)

        self.stream = self.p.open(
            # output_device_index=0,
            format=format,
            channels=channels,
            rate=rate,
            output=True,
            stream_callback=lambda in_data, frame_count, time_info, status: self.read(
                in_data, frame_count, time_info, status),
            start=False
        )

    def write(self, bytes):
        if (len(self.buffer) + len(bytes)) > self.max_buffer_size:
            n = int(len(self.buffer) + len(bytes) - self.max_buffer_size)
            self.buffer = bytes
            # return
        else:
            self.buffer += bytes
        if not self.started and len(self.buffer) >= self.min_buffer_size:
            self.stream.start_stream()
            self.started = True
        # print("WRITE:", len(self.buffer))

    def read(self, in_data, frame_count, time_info, status):
        N = frame_count * self.width * self.channels
        data = self.buffer[0:N]
        self.buffer = self.buffer[N::]
        n = len(data)
        if (n < N):
            data += b'\x00' * (N-n)
        # print("READ:", len(self.buffer))
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
            width=self.width,
            channels=self.nchannels,
            rate=self.rate
        )

    def tick(self, pixels, time_delta):
        if (time_delta > 1):
            return
        self.time_sum += time_delta
        read = min(int(self.time_sum * self.rate - self.frame),
                   self.nframes - self.frame)
        if read == 0:
            print("CLOSED")
            self.wavfile.close()
            self.playback.close()
            self.type = STATIC
            return
        self.frame += read
        data = self.wavfile.readframes(read)
        self.playback.write(data)

    def clone(self):
        return PlayMusic(self.wavfile, self.playback)


class PlayMusicStream(BaseEffect):
    def __init__(self,
                 stream,
                 playback=None,
                 width=4,
                 nchannels=1,
                 rate=44100):
        super().__init__(type=DYNAMIC)
        self.stream = stream

        self.width = width
        self.nchannels = nchannels
        self.rate = rate
        self.time_sum = 0
        self.index = 0

        if playback is None:
            self.playback = PyAudioPlayer()
        else:
            self.playback = playback

        self.playback.setup(
            width=self.width,
            channels=self.nchannels,
            rate=self.rate,
            format_override=pyaudio.paInt32
        )

    def tick(self, pixels, time_delta):
        if (time_delta > 1):
            # print("ESCAPED")
            return
        # print(time_delta)
        self.time_sum += time_delta
        read = int(self.time_sum * self.rate *
                   self.width * self.nchannels) - self.index

        if self.stream.closed:
            print("CLOSED")
            self.playback.close()
            self.type = STATIC
            return

        data = self.stream.read(read)
        self.index += len(data)
        self.playback.write(data)

    def clone(self):
        return PlayMusicStream(self.stream, self.playback, self.width, self.nchannels, self.rate)


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

        self.fade = None

        self.closed = False

        self.playback = playback
        if self.playback is not None:
            self.playback.setup(
                width=self.width,
                channels=self.nchannels,
                rate=self.rate
            )

    def tick(self, pixels, time_delta):
        if (time_delta > 1):
            return
        # print(time_delta)
        self.time_sum += time_delta
        read = min(int(self.time_sum * self.rate - self.frame),
                   self.nframes - self.frame)
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
        bins, self.threshold = fft(values, read, self.rate, self.nbins, self.min_freq,
                                   self.max_freq, self.linear, time_delta, self.threshold, self.fade)

        color = clone_pixels(pixels)
        self.color.tick(color, time_delta)
        N = len(color)

        fill_pixels_from_bins(bins, self.nbins, pixels, N, color,)

    def clone(self):
        return SpectrumEffect(self.color, self.wavfile, self.playback, self.linear, self.nbins, self.min_freq, self.max_freq)


class SpectrumEffectStream(BaseEffect):
    def __init__(self,
                 color,
                 stream,
                 playback=None,
                 linear=True,
                 nbins=37,
                 min_freq=115,
                 max_freq=900,
                 width=4,
                 nchannels=1,
                 rate=44100):

        super().__init__(type=DYNAMIC)
        self.stream = stream
        self.color = color

        self.width = width
        self.nchannels = nchannels
        self.rate = rate

        self.time_sum = 0
        self.index = 0

        self.threshold = 1E7
        self.nbins = nbins
        self.min_freq = min_freq
        self.max_freq = max_freq
        self.linear = linear

        self.fade = [0 for i in range(self.nbins)]

        self.closed = False

        self.playback = playback
        if self.playback is not None:
            self.playback.setup(
                width=self.width,
                channels=self.nchannels,
                rate=self.rate,
                format_override=pyaudio.paInt32
            )

    def tick(self, pixels, time_delta):
        if (time_delta > 0.1):
            # print("ESCAPED")
            return
        self.time_sum += time_delta
        # print(time_delta)
        read = int(self.time_sum * self.rate *
                   self.width * self.nchannels) - self.index
        read = int(read / 4) * 4

        if self.stream.closed:
            print("CLOSED")
            self.playback.close()
            self.type = STATIC
            return

        data = self.stream.read(read)
        self.index += read

        if self.playback is not None:
            self.playback.write(data)

        values = np.frombuffer(data, dtype="<i4")
        bins, self.threshold = fft(values, read, self.rate, self.nbins, self.min_freq,
                                   self.max_freq, self.linear, time_delta, self.threshold, self.fade)

        color = clone_pixels(pixels)
        self.color.tick(color, time_delta)
        N = len(color)

        fill_pixels_from_bins(bins, self.nbins, pixels, N, color)

    def clone(self):
        return SpectrumEffectStream(self.color, self.stream, self.playback, self.linear, self.nbins, self.min_freq, self.max_freq, self.width, self.nchannels, self.rate)
