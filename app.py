from flask import Flask, request, render_template, send_from_directory
import pyaudio
import wave
import os
import pyaudio, wave, time, sys
from datetime import datetime
from recorder import Recorder

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "recordings"
# Get Mixer ID
mixer_name = "Speak"
mixer_channels = 0
mixer_id = None
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    if mixer_name in dev['name']:
        mixer_id = i
        mixer_channels = dev["maxOutputChannels"]
        try:
            rec = Recorder(channels = mixer_channels, input_device_index = mixer_id)
        except Exception as e:
            print(f"{e} \nFailed to Load Mixer Device {dev}")

if mixer_id == None:
    print("Mixer Not Found")
    exit()

open_file = None 

@app.route('/download/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    uploads = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    return send_from_directory(directory=uploads, filename=filename, as_attachment=True)

@app.route('/delete/<path:filename>', methods=['GET', 'POST'])
def delete(filename):
    uploads = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    return send_from_directory(directory=uploads, filename=filename, as_attachment=True)

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
                open_file.close()
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
    app.run(host='0.0.0.0', port='5000', debug=True)