import pyaudio
import wave
import threading


class AudioRecorder():


    # Audio class based on pyAudio and Wave
    def __init__(self):

        self.__open = True
        self.__rate = 44100
        self.__frames_per_buffer = 1024
        self.__channels = 2
        self.__format = pyaudio.paInt16
        self.__audio_filename = "temp_audio.wav"
        self.__audio = pyaudio.PyAudio()
        self.__stream = self.__audio.open(format=self.__format,
                                      channels=self.__channels,
                                      rate=self.__rate,
                                      input=True,
                                      input_device_index=2,
                                      frames_per_buffer = self.__frames_per_buffer)
        self.__audio_frames = []
        self.__curr_audio_frames = []


    # Audio starts being recorded
    def record(self):

        self.__stream.start_stream()
        
        while self.__open:
            data = self.__stream.read(self.__frames_per_buffer) 
            self.__audio_frames.append(data)
            self.__curr_audio_frames.append(data)


    # Finishes the audio recording therefore the thread too    
    def stop(self):

        if self.__open:
            self.__open = False
            self.__stream.stop_stream()
            self.__stream.close()
            self.__audio.terminate()

            waveFile = wave.open(self.__audio_filename, 'wb')
            waveFile.setnchannels(self.__channels)
            waveFile.setsampwidth(self.__audio.get_sample_size(self.__format))
            waveFile.setframerate(self.__rate)
            waveFile.writeframes(b''.join(self.__audio_frames))
            waveFile.close()


    # Launches the audio recording function using a thread
    def start(self):
        audio_thread = threading.Thread(target=self.record)
        audio_thread.start()
        
    
    def clear_buffer(self):
        self.__curr_audio_frames.clear()
        
        
    def read_buffer(self):
        return self.__curr_audio_frames
