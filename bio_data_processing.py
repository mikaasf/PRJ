import csv
import numpy as np
from scipy import signal as sg
from server_pages import insert, generate_json_range


def read_data_from_csv(filename: str, path:str = None) -> np.ndarray:
    if path:
        filename = path + filename
        
    with open(filename) as file:
        csv_data = csv.reader(file)

        data = []
        line_count = 0
        
        for row in csv_data:
            if line_count:
                data.append(float(row[0]))
            line_count += 1

        return np.array(data)
    
def ppg_signal_processing(data: np.ndarray) -> np.ndarray:
    diff_data = np.diff(data) ** 2
    diff_data_norm = diff_data / np.max(diff_data)
    diff_data_clip = np.where(diff_data_norm > .4, diff_data_norm, 0)
    return sg.find_peaks(diff_data_clip)[0]

def calculate_bpm(peaks: np.ndarray, sampling_rate: int, start_timestamp: float) -> list:
    bpm_w_timestamps = []

    current_timestamp = start_timestamp
    for i in range(1, peaks.size):
        if i + 1 != peaks.size:
            current_timestamp += 1 / sampling_rate
            bpm = sampling_rate / (peaks[i + 1] - peaks[i]) * 60
            bpm_w_timestamps.append((current_timestamp, int(np.round(bpm))))
            
    return bpm_w_timestamps

def send_bpm_data_to_db(bpm_list:list, id_video:int, sampling_rate: int) -> None:
    for bpm_tuple in bpm_list:
        insert("INSERT INTO sensorData(dataType, iniTime, idVideo, valueData, duration) VALUES (%s, %s, %s, %s, %s)", 
               ["BPM", bpm_tuple[0], id_video, bpm_tuple[1], 1. / sampling_rate])
        
    generate_json_range(id_video)


if __name__ == "__main__":
    
    data = read_data_from_csv("ppg_signal.csv")
    peaks = ppg_signal_processing(data)
    bpm_list = calculate_bpm(peaks, 50, 50)
    send_bpm_data_to_db(bpm_list, 1, 50)