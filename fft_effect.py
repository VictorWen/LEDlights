from effects import *
import wave
import numpy as np
from numpy.fft import rfft, rfftfreq
from scipy.fftpack import next_fast_len
# import discord_comms as dc

def scale_freq(ints, freqs, offset, cap, N, bins):
    results = np.array([0 for k in range(N)])
    x = (cap / offset) ** (1/bins)
    bin_size = N / bins
    freq = offset
    j = 0
    bin_count = 0
    while bin_count < N:
        sum = 0
        count = 0
        next = bin_count + bin_size
        while freqs[j] <= freq:
            sum += ints[j]
            count += 1
            j += 1
        if count > 0:
            avg = sum / count
            for i in range(int(bin_count), int(next)):
                results[i] = avg

        freq *= x
        bin_count = next
    return results


class FFTEffect(BaseEffect):
    def __init__(self, file, multiplier=15, playback=None):
        super().__init__(type=DYNAMIC)
        self.audio = wave.open(file, 'rb')
        self.rate = self.audio.getframerate()
        self.nframes = self.audio.getnframes()
        # self.multiplier = multiplier
        print(self.rate, self.nframes, self.nframes / self.rate / 60)
        self.frame = 0
        self.max = 1E6
        self.playback = playback
        self.playback_state = None

    def __del__(self):
        self.audio.close()
    
    def tick(self, pixels, time_delta):
        if (self.frame >= self.nframes):
            self.type = STATIC
            return

        N = len(pixels)
        read = min(int(self.rate * time_delta), self.nframes - self.frame)
        if (read == 0): return
        
        bdata = self.audio.readframes(read)
        data = np.frombuffer(bdata, dtype="<i2")
        length = next_fast_len(read)

        if self.playback is not None:
            # bdata, self.playback_state = audioop.ratecv(bdata, 2, 1, self.rate, 48000, self.playback_state)
            self.playback.write(bdata)
        
        intensities = rfft(data, length)
        freq = rfftfreq(length, 1/self.rate)
       
        intensities = np.abs(intensities)
        intensities = scale_freq(intensities, freq, 40, 1000, N, 50)
        self.max = 0.9 * self.max + 0.1 * np.max(intensities)
        
        values = intensities / self.max

        self.frame += read

        for i in range(N):
            pixels[i] = RGB(1 - min(1, values[i]))
        pixels.show()
