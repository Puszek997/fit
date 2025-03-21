import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
import utils as ut
from datetime import datetime as dt


measurements, floors = ut.fileImport(
    r"C:\Users\mateu\Documents\programowanie\fit\reads"
)
# pre-processing step (essential for all functions to work)
measurements = ut.measurement_prep(measurements, floors)

# noise floor mean value(average)
baselines = ut.calculate_baselines(measurements)

median = ut.calculate_median(measurements)

# we take mean value as our pseudo noise free value and them subtract it from every value to get noise
# for every measurement we take noise estimates and calculate noise variances
# after that we find variances across multiple meausurements

# analysis after that

# noise and variance per measurement (_i) and per place
# std - standard deviation
variances, mean_variance, std_variance = ut.calculate_noise(baselines, measurements)
# array of wavelets from measurements
wavelets = ut.wavelet_transform(measurements)

# array of reconstructed data
reconstruced_data = ut.reconstruct_from_wavelet(wavelets)

# calculating distortions of each measurement
distortion = ut.calculate_distortion(measurements)


# noise and variance per measurement (_i) and per place taken from the wavelet vectors
variances_wave, mean_variance_wave, std_variance_wave = ut.calculate_noise(
    baselines, reconstruced_data
)

# function used to sample the given data at a base frequency/n
n=2
measurements_changed = ut.change_sampling(n, measurements)

### PLOT ###

y = measurements[1][12][2]["RSSI"]
print(ut.spectral_flatness(y))
x = np.linspace(0, y.size, y.size)

fig1, ax1 = plt.subplots()
ax1.plot(x, y, label="RSSI", antialiased=True, color="blue")
plt.title("4.10 at 50 Hz")
ax1.set_xlabel("Data Point")
ax1.set_ylabel("RSSI value")

### wavelet overlay ###
# ax2= ax1.twinx()
# ax2.plot(x, reconstruced_data[4][10]["RSSI"], label='Wavelet reconstruction', color='red', antialiased=True)
# ax2.set_ylabel('Noise value', color='red')
# ax2.tick_params(axis='y', labelcolor='red')

plt.show()
