import os
import ffmpeg
import uuid
from deepspeech.model import Model
import scipy.io.wavfile as wav
from flask import Flask, flash, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = set(['wav', 'mp3', 'flac'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ds = Model('models/output_graph.pb', 26, 9, 'models/alphabet.txt', 500)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            fileLocation = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(fileLocation)
            convertedFile = normalize_file(fileLocation)
            os.remove(fileLocation)
            return redirect(url_for('transcribe',
                                    filename=convertedFile))
    return '''
    <!doctype html>
    <center><title>Upload an Audio File</title>
    <h1>Upload your audio file</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    <br>
    <p>We accept wav, mp3 and flac, after uploading you'll be redirected to a transcribed version of your file.</p>
    <p>No state is retained by this application, we use Mozilla's DeepSpeech library with their default models and settings,
    To contribute, come check out our code here! We're also looking for suggestions as how to improve accuracy.</p></center>
    '''

@app.route('/results/<filename>')
def transcribe(filename):
    fs, audio = wav.read(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    processed_data = ds.stt(audio, fs)
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return processed_data

# Use ffmpeg to convert our file to WAV @ 16k
def normalize_file(file):
    filename = str(uuid.uuid4()) + ".wav"
    fileLocation = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    stream = ffmpeg.input(file)
    stream = ffmpeg.output(stream, fileLocation, acodec='pcm_s16le', ac=1, ar='16k')
    # stream = ffmpeg.overwrite_output(stream)
    ffmpeg.run(stream)
    return filename
