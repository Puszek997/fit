import json
from os import listdir
from os.path import isfile, join
import numpy as np
from datetime import datetime as dt
import random
import scipy.signal as signal
import pywt

N = 20


def fileImport(dir):
    measurements = [
        [[None for _ in range(N)] for _ in range(20)] for _ in range(6)
    ]  # [floor][place][measurement index]{Speed, RSSI, Noise, Date, Time}
    measurement_count = [[0  for _ in range(20)] for _ in range(6)]

    files = [f for f in listdir(dir) if isfile(join(dir, f))]
    for i in measurement_count:
        for y in i:
         
                z = 0

    for floor in range(1, 5, 1):

        for place in range(1, 20, 1):

            for i in range(1, N, 1):

                name = f"{floor}.{place}.{i}.json"
                measurements[floor][place][i] = findFile(name, files, dir)
                if measurements[floor][place][i] != None:
                    measurement_count[floor][place] = (
                        measurement_count[floor][place] + 1
                    )

   
    return measurements, measurement_count

def measurement_prep(measurements, measurement_count):

    averaged = [[None for _ in range(20)] for _ in range(5)]

    for fl in range(1, 5, 1):

        for pl in range(1, 20, 1):

            rssi = np.array([])
            noise = np.array([])
            speed = np.array([])
            begin=True
            for me in range(1, N, 1):

                if measurements[fl][pl][me] == None:
                    continue
                else:
                    if begin:
                        rssi =  measurements[fl][pl][me]["RSSI"]
                        noise = measurements[fl][pl][me]["Noise"]
                        speed = measurements[fl][pl][me]["Speed"]
                        begin = False
                        continue
                    rssi = rssi + measurements[fl][pl][me]["RSSI"]
                    noise =noise + measurements[fl][pl][me]["Noise"]
                    speed = speed+ measurements[fl][pl][me]["Speed"]

            pseudo_baseline_r = rssi/measurement_count[fl][pl]
            pseudo_baseline_n = noise/measurement_count[fl][pl]
            pseudo_baseline_s = speed/measurement_count[fl][pl]
            averaged[fl][pl] = {
                "RSSI": pseudo_baseline_r,
                "Noise": pseudo_baseline_n,
                "Speed": pseudo_baseline_s,
            }
    return averaged


def spectral_flatness(noisy_signal, fs=1000):
    f, psd = signal.welch(noisy_signal, fs, nperseg=256)
    geometric_mean = np.exp(np.mean(np.log(psd + 1e-10)))  # Avoid log(0)
    arithmetic_mean = np.mean(psd)
    return geometric_mean / arithmetic_mean

def findFile(names, files, dir):
    found = False
    ind = 0
    for i in files:

        if i == names:
            with open(dir + r"/" + names, "r") as file:
                data = json.load(file)
                found = True
                files.pop(ind)
                break
        ind += 1
    if found == False:
        return None

    RS = []
    N = []
    TR = []
    date_obj = dt.fromisoformat(data[0]["date"])

    time = date_obj.time().strftime("%H")
    date = date_obj.date()

    for i in range(100):

        RS.insert(1, data[i]["rssi"])
        N.insert(1, data[i]["noise"])
        TR.insert(1, data[i]["transmit_rate"])

    Noise = np.array(N)
    RSSI = np.array(RS)
    Speed = np.array(TR)

    return {
        "Name": names,
        "Noise": Noise,
        "RSSI": RSSI,
        "Speed": Speed,
        "Date": date,
        "Time": time,
    }


def signaltonoise_dB(a, axis=0, ddof=0):
   
    m = a.mean(axis)
    sd = a.std(axis=axis, ddof=ddof)

    if sd == 0:
        return 1000000
    r =  20 * np.log10(abs(np.where(sd == 0, 0, m / sd)))

    return r

def change_sampling(n,measurements):
    n=int(n)

    measurements_changed = [
        [[None for _ in range(N)] for _ in range(20)] for _ in range(6)
     ]
    
    for fl in range(1, 5, 1):
        for pl in range(1, 20, 1):
            if measurements[fl][pl] == None or measurements[fl][pl]["RSSI"].size==0:
                    continue
            rs= np.array([])
            sp = np.array([])
            no=np.array([])
            for i in range(0,99,1):          
                if i%n==0:
                    rs = np.append(rs, measurements[fl][pl]["RSSI"][i])
                    sp=np.append(sp,measurements[fl][pl]["Speed"][i])
                    no=np.append(no,measurements[fl][pl]["Noise"][i])
            measurements_changed[fl][pl]={"RSSI" : rs,
                    "Noise" : no,
                    "Speed" : sp}
                    
    return measurements_changed

def calculate_baselines(measurements):

    baselines = [[None for _ in range(20)] for _ in range(5)]

    for fl in range(1, 5, 1):

        for pl in range(1, 20, 1):
            if measurements[fl][pl]== None:
                    continue
            rssi =  measurements[fl][pl]["RSSI"]
            noise =  measurements[fl][pl]["Noise"]
            speed =  measurements[fl][pl]["Speed"]
            pseudo_baseline_r = np.mean(rssi, axis=0)
            pseudo_baseline_n = np.mean(noise, axis=0)
            pseudo_baseline_s = np.mean(speed, axis=0)

            baselines[fl][pl] = {
                "RSSI": pseudo_baseline_r,
                "Noise": pseudo_baseline_n,
                "Speed": pseudo_baseline_s,
            }
    return baselines


def calculate_noise(baselines, measurements):

    
    variances = [[None for _ in range(20)] for _ in range(6)]
    mean_variance = [[None for _ in range(20)] for _ in range(6)]
    std_variance = [[None for _ in range(20)] for _ in range(6)]

    for fl in range(1, 5, 1):
        for pl in range(1, 20, 1):
            if measurements[fl][pl] == None:
                    continue
            noise_r = measurements[fl][pl]["RSSI"] - baselines[fl][pl]["RSSI"]
            noise_s = measurements[fl][pl]["Speed"] - baselines[fl][pl]["Speed"]
            noise_n = measurements[fl][pl]["Noise"] - baselines[fl][pl]["Noise"]

            variance_r = np.var(noise_r)
            variance_s = np.var(noise_s)
            variance_n = np.var(noise_n)


            variances[fl][pl] = {
                "RSSI": np.var(variance_r),
                "Noise": np.var(variance_n),
                "Speed": np.var(variance_s),
            }
            mean_variance[fl][pl] = {
                "RSSI": np.mean(variance_r),
                "Noise": np.mean(variance_n),
                "Speed": np.mean(variance_s),
            }
            std_variance[fl][pl] = {
                "RSSI": np.std(variance_r),
                "Noise": np.std(variance_n),
                "Speed": np.std(variance_s),
            }
    return  variances, mean_variance, std_variance


def wavelet_transform(measurements):

    wavelets = [[None for _ in range(20)] for _ in range(6)]
    waveletType = "coif5"

    for fl in range(1, 5, 1):
        for pl in range(1, 20, 1):

           
            if measurements[fl][pl] == None or measurements[fl][pl]["RSSI"].shape==(0,):
                continue

            wavelets[fl][pl]= {
                "RSSI": pywt.wavedec(
                    measurements[fl][pl]["RSSI"], waveletType, level=3
                ),
                "Noise": pywt.wavedec(
                    measurements[fl][pl]["Noise"], waveletType, level=3
                ),
                "Speed": pywt.wavedec(
                    measurements[fl][pl]["Speed"], waveletType, level=3                   ),
            }
                

    return wavelets


def reconstruct_from_wavelet(wavelets, n =100):
   

    waveletType = "coif5"
    reconstructed_data = [
        [None  for _ in range(20)] for _ in range(6)
    ]

    for fl in range(1, 5, 1):
        for pl in range(1, 20, 1):

           
            if wavelets[fl][pl]== None:
                continue
            coeffs_r = wavelets[fl][pl]["RSSI"]
            coeffs_n = wavelets[fl][pl]["Noise"]
            coeffs_s = wavelets[fl][pl]["Speed"]

            # setting thresholds
            threshold_r = np.std(coeffs_r[-1]) * np.sqrt(2 * np.log(n)) * 1.2
            threshold_n = np.std(coeffs_n[-1]) * np.sqrt(2 * np.log(n)) * 1.2
            threshold_s = np.std(coeffs_s[-1]) * np.sqrt(2 * np.log(n)) * 1.2

            # aplying thresholding (denoising of wavelets) - we delete the small coefficients
            coeff_den_r = [
                pywt.threshold(c, value=threshold_r, mode="soft") if i > 0 else c
                for i, c in enumerate(coeffs_r)
            ]
            coeff_den_s = [
                pywt.threshold(c, value=threshold_s, mode="soft") if i > 0 else c
                for i, c in enumerate(coeffs_s)
            ]
            coeff_den_n = [
                pywt.threshold(c, value=threshold_n, mode="soft") if i > 0 else c
                for i, c in enumerate(coeffs_n)
            ]

            est_clean_r = pywt.waverec(coeff_den_r, waveletType)
            est_clean_n = pywt.waverec(coeff_den_n, waveletType)
            est_clean_s = pywt.waverec(coeff_den_s, waveletType)

            reconstructed_data[fl][pl] = {
                "RSSI": np.array(est_clean_r),
                "Noise": np.array(est_clean_n),
                "Speed": np.array(est_clean_s),
            }

    return reconstructed_data



def calculate_distortion(measurements):
    distortions = [
        [None  for _ in range(20)] for _ in range(6)
    ]
    for fl in range(1, 5, 1):
        for pl in range(1, 20, 1):
            
            if not isinstance(measurements[fl][pl], dict):  # Ensure it's a dictionary
                continue
            distortions[fl][pl]={
                "RSSI":  spectral_flatness(measurements[fl][pl]["RSSI"]),
                "Noise": spectral_flatness(measurements[fl][pl]["Noise"]),
                "Speed": spectral_flatness(measurements[fl][pl]["Speed"]),
            }
                

    return distortions



def calculate_median(measurements):

    baselines = [[None for _ in range(20)] for _ in range(5)]

    for fl in range(1, 5, 1):

        for pl in range(1, 20, 1):

           

           

            if measurements[fl][pl] == None:
                continue
            else:
                rssi = measurements[fl][pl]["RSSI"]
                noise = measurements[fl][pl]["Noise"]
                speed = measurements[fl][pl]["Speed"]

            pseudo_baseline_r = np.median(rssi, axis=0)
            pseudo_baseline_n = np.median(noise, axis=0)
            pseudo_baseline_s = np.median(speed, axis=0)

            baselines[fl][pl] = {
                "RSSI": pseudo_baseline_r,
                "Noise": pseudo_baseline_n,
                "Speed": pseudo_baseline_s,
            }
    return baselines