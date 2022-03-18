import wave
import numpy as np
from scipy.fftpack import fft, fftfreq

tps = 20

def compress(data, target_size):
    n = len(data)
    frame_size = int(n / target_size)
    # print(frame_size)
    i = 0
    result = np.array([0 for x in range(target_size)])
    # print(data[0 : frame_size])
    while i < target_size:
        k = i * frame_size
        values = data[k : min(k + frame_size, n)]
        # print(values)
        result[i] = np.mean(values)
        i += 1
    return result

with wave.open("test.wav", 'rb') as audio:
    rate = int(audio.getframerate() / tps)
    nframes = audio.getnframes()
    frame = 0
    while frame < nframes:
        data = audio.readframes(rate)
        data = np.frombuffer(data, dtype="<i2")
        intensities = np.fft.rfft(data)
        intensities = np.abs(intensities)
        # print(intensities)
        intensities = compress(intensities, 100)

        frame += rate

        print(intensities)
        # break