from flask import Flask, request, render_template
import pyaudio
import wave
import os
import pyaudio, wave, time, sys
from datetime import datetime

class Recorder(object):
    '''A recorder class for recording audio to a WAV file.
    Records in mono by default.
    '''

    def __init__(self, channels=1, rate=44100, frames_per_buffer=8192, input_device_index = 0):
        self.channels = channels
        self.rate = rate
        self.input_device_index = input_device_index
        self.frames_per_buffer = frames_per_buffer

    def open(self, fname, mode='wb'):
        return RecordingFile(fname, mode, self.input_device_index, self.channels, self.rate,
                            self.frames_per_buffer)

class RecordingFile(object):
    def __init__(self, fname, mode, input_device_index, channels, 
                rate, frames_per_buffer):
        self.fname = fname
        self.mode = mode
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self._pa = pyaudio.PyAudio()
        self.input_device_index = input_device_index
        self.wavefile = self._prepare_file(self.fname, self.mode)
        self._stream = None

    def __enter__(self):
        return self

    def __exit__(self, exception, value, traceback):
        self.close()

    def record(self, duration):
        # Use a stream with no callback function in blocking mode
        self._stream = self._pa.open(format=pyaudio.paInt16,
                                        channels=self.channels,
                                        rate=self.rate,
                                        input=True,
                                        frames_per_buffer=self.frames_per_buffer)
        for _ in range(int(self.rate / self.frames_per_buffer * duration)):
            audio = self._stream.read(self.frames_per_buffer)
            self.wavefile.writeframes(audio)
        return None

    def start_recording(self):
        # Use a stream with a callback in non-blocking mode
        self._stream = self._pa.open(format=pyaudio.paInt16,
                                        channels=self.channels,
                                        rate=self.rate,
                                        input=True,
                                        frames_per_buffer=self.frames_per_buffer,
                                        input_device_index = self.input_device_index,
                                        stream_callback=self.get_callback())
        self._stream.start_stream()
        return self

    def stop_recording(self):
        self._stream.stop_stream()
        return self

    def get_callback(self):
        def callback(in_data, frame_count, time_info, status):
            self.wavefile.writeframes(in_data)
            return in_data, pyaudio.paContinue
        return callback


    def close(self):
        self._stream.close()
        self._pa.terminate()
        self.wavefile.close()

    def _prepare_file(self, fname, mode='wb'):
        wavefile = wave.open(fname, mode)
        wavefile.setnchannels(self.channels)
        wavefile.setsampwidth(self._pa.get_sample_size(pyaudio.paInt16))
        wavefile.setframerate(self.rate)
        return wavefile

app = Flask(__name__)
# Get Mixer ID
mixer_name = "USB"
mixer_id = 0
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
  dev = p.get_device_info_by_index(i)
  if mixer_name in dev['name']:
      mixer_id = i

rec = Recorder(channels = 2, input_device_index = mixer_id)

open_file = None 
# TODO Add filename update
@app.route('/', methods=['GET', 'POST'])
def hello_world():
    global open_file, fileList
    state = "off"
    name = "Start Recording"
    if request.method == 'POST':
        if request.form['button'] == 'on':
            state, name = "off", "Start Recording"
            if open_file != None:
                open_file.stop_recording()
            print('Stopped Recording')
        if request.form['button'] == 'off':
            state, name = "on", "Stop Recording"
            current_time = str(datetime.now())  #"Date/Time for File Name"
            current_time = "_".join(current_time.split()).replace(":","-")
            current_time = current_time[:-7]
            WAVE_OUTPUT_FILENAME = "recordings/"+'Audio_'+current_time+'.wav'

            open_file = rec.open(WAVE_OUTPUT_FILENAME, 'wb')
            open_file.start_recording()
            print('Started Recording')
    fileList = os.listdir("recordings")
    return render_template("index.html",state=state, name=name, fileList=fileList)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000')