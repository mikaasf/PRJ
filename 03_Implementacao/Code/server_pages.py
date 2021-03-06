import cv2
import flask
import json
import numpy as np
import os
import re
import secrets
import subprocess
import time
import urllib
from datetime import datetime
from deepface_vid_processing import DeepFaceClassifier
from flask import Flask, render_template, request, redirect, url_for, make_response, session, Response, jsonify
from flaskext.mysql import MySQL
from flask_socketio import SocketIO
from send_frame_handler import SendFrame
from urllib.parse import urlparse, urljoin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pathlib
import platform

TEMP_DIRECTORY = os.path.join(".", "static", "temp")  # "./static/temp"
UPLOAD_DIRECTORY = os.path.join(".", "static", "videos")  # "./static/videos"
JSON_DIRECTORY = os.path.join(UPLOAD_DIRECTORY, "json")  # UPLOAD_DIRECTORY + "/json"
THUMBNAILS_DIRECTORY = os.path.join(UPLOAD_DIRECTORY, "thumbnails")  # UPLOAD_DIRECTORY + "/thumbnails"

if not os.path.exists(TEMP_DIRECTORY):
    os.makedirs(TEMP_DIRECTORY)

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

if not os.path.exists(JSON_DIRECTORY):
    os.makedirs(JSON_DIRECTORY)

if not os.path.exists(THUMBNAILS_DIRECTORY):
    os.makedirs(THUMBNAILS_DIRECTORY)

ALLOWED_EXTENSIONS = {'mpeg', 'mp4'}
# ==================================
# ==== APP INITIALIZATION PARAMETERS ====
app = Flask(__name__)
app.secret_key = secrets.token_bytes(16)

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'projeto'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
# file upload configurations
app.config['UPLOAD_FOLDER'] = UPLOAD_DIRECTORY
app.config['MAX_CONTENT_LENGTH'] = 256 * 1024 * 1024  # 256 mb

db = MySQL()
db.init_app(app)
db_con = db.connect()

socketio = SocketIO(app, cors_allowed_origins="*")
com_socket_handler = None


# ==================================
# ==== DATABASE FUNCTIONS ====


def get_cursor_db():
    db_con.autocommit(True)
    return db_con.cursor()


def execute_one_query(query: str, params: list = None, fetchall: bool = False):
    """ Call this function with the query SQL as first parameter
    @param query SQL query
    @param params list of custom values for % values in the query
    @param fetchall True for getting every result, False to get the first only """
    try:
        cursor = get_cursor_db()
        cursor.execute(query, params)
        if fetchall:
            result = cursor.fetchall()
        else:
            result = cursor.fetchone()
        db_con.commit()
        cursor.close()
        print(query)
    except Exception as e:
        print("Problem accessing database - error: " + str(e))
        return False
    return result


def insert(query: str, params: list = None):
    """ Call this function with the query SQL Insert as first parameter
        @param query SQL Insert query
        @param params list of custom values for % values in the query """
    try:
        cursor = get_cursor_db()
        result = cursor.execute(query, params)
        db_con.commit()
        cursor.close()
        print(query)
    except Exception as e:
        print("Problem inserting into db: " + str(e))
        return False
    return result


# ==================================
# ==== LOGIN METHODS ====


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@app.route('/login', methods=['POST', 'GET'])
def login():
    if 'username' in session:
        return redirect(url_for('myvideos'))
    error = None
    if request.method == 'POST':
        username = request.form['your_name']
        password = request.form['your_pass']
        remember = request.form['remember-me']
        if 'username' in request.cookies:
            username = request.cookies.get('username')
            password = request.cookies.get('password')
            print("From cookies")
            if valid_login(username, password):
                if not is_safe_url(request.args.get('next')):
                    flask.abort(400)
                print("Logged in!")
                return log_the_user_in(username)
        elif 'your_name' in request.form and 'your_pass' in request.form:
            if remember:
                resp = make_response(redirect('/home'))
                resp.set_cookie('username', username, max_age=3600)
                resp.set_cookie('password', password, max_age=3600)
                resp.set_cookie('remember', remember, max_age=3600)
            if valid_login(username,
                           password):
                if not is_safe_url(request.args.get('next')):
                    flask.abort(400)

                print("Logged in!")
                return log_the_user_in(username)

        error = 'Invalid username/password'

    # the code below is executed if the request method
    # was GET or the credentials were invalid

    return render_template('login.html', page='login', error=error)


def log_the_user_in(username: str):
    """ Function to login and redirect the user
    @param username username of the user who logged in """
    session['username'] = username
    # admin = execute_one_query("SELECT adm FROM person WHERE username = %s", username)
    return redirect(url_for('myvideos'))


def valid_login(username: str, password: str) -> bool:
    """ Function to check if login credentials are valid in the database
    @param username username of the user who wants to log in
    @param password password of the user who wants to log in """
    account = execute_one_query("SELECT * FROM person WHERE username = %s", username)
    return account and check_password_hash(account[1], password)


def get_user_data():
    """ Function to get the username and email of who is logged in """
    username = session['username']
    return username, execute_one_query("SELECT email FROM person WHERE username = %s", username)[0]


# ==================================
# ==== LOGOUT METHOD ====


@app.route('/logout')
def logout():
    """ Function to log out the logged user and redirect to login page"""
    # remove the username from the session if it's there
    if 'username' in session:
        session.pop('username', None)
        session.pop('password', None)
    return redirect(url_for('login'))


# ==================================
# ==== SIGNUP METHODS ====


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if 'username' in session:
        return redirect(url_for('myvideos'))
    error = None
    if request.method == 'POST':
        if 'name' in request.form and 'pass' in request.form and 'email' in request.form and 're_pass' in request.form:
            if len(request.form['pass']) < 6:
                error = 'Password must have 6 ou more characters'
            else:
                if request.form['pass'] == request.form['re_pass']:
                    username = request.form['name']
                    email = request.form['email']
                    password = request.form['pass']
                    if valid_registration(email, username):
                        register_user(username, password, email)
                        return log_the_user_in(username)
                    else:
                        error = 'That e-mail or username is already registered'
                elif request.form['pass'] is not "":
                    error = 'Passwords don\'t match'

        # the code below is executed if the request method
        # was GET or the credentials were invalid
    return render_template('signup.html', page='signup', error=error)


def valid_registration(email: str, username: str) -> bool:
    """ Function to check if username and email in registration are available and valid """
    account = execute_one_query("SELECT * FROM person WHERE email = %s OR username = %s", [email, username])
    if account:
        return False
    elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
        return False
    elif not re.match(r'[A-Za-z0-9]+', username):
        return False
    return True


def register_user(username: str, password: str, email: str):
    """ Function to insert the new user in database """
    insert("INSERT INTO person values (%s, %s, %s, %r)", [username, generate_password_hash(password), email, True])


# ==================================
# ==== MAIN PAGES METHODS ====

def ext_generate():
    global com_socket_handler
    while True:
        frame = com_socket_handler.get_buffer
        if frame:
            frame = com_socket_handler.get_buffer.pop()
            if frame[0]:
                img = cv2.imencode('.jpg', frame[1])[1].tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + img + b'\r\n')


def ext_generate_cam():
    global com_socket_handler
    while True:
        frame = com_socket_handler.get_buffer
        if frame:
            frame = com_socket_handler.get_buffer.pop()
            img = cv2.imencode('.jpg', frame)[1].tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + img + b'\r\n')


def generate_test_img():
    frame = cv2.imread("./static/imgs/eyeLogo.png")
    frame = cv2.imencode('.jpg', frame)[1].tobytes()
    return (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


# ---- PARA WEBCAM LOCAL -----
def gen():
    """Video streaming generator function."""
    camera = cv2.VideoCapture(0)
    while True:
        flag, img = camera.read()
        img = cv2.imencode('.jpg', img)[1].tobytes()
        if flag:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + img + b'\r\n')


@app.route('/video')
def video():
    return Response(ext_generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/", methods=['GET', 'POST'])
def home():
    global com_socket_handler
    if com_socket_handler:
        com_socket_handler.close_socket()
    if request.method == 'POST':
        if 'vid_title' in request.form:
            vid_title = request.form['vid_title']
        else:
            vid_title = "Untitled"
        print("title", vid_title)
        recTime = time.strftime("%Y-%m-%d %H:%M:%S")
        if 'loc' in request.form:
            location = request.form['loc']
        else:
            location = ""
        id_video = session['idVideo']
        generate_json_range(id_video)
        # insert_video_db(session['username'], None, "video_" + str(id_video) + ".mp4", recTime, location, vid_title, session['idVideo'], False)
        return redirect(url_for('myvideos'))
    if 'username' in session:
        if not com_socket_handler:
            session['idVideo'] = get_and_increment_current_video_id()
            com_socket_handler = SendFrame(socketio, session['idVideo'], create_thumbnail)
            com_socket_handler.start()
        return render_template("page.html", page='on_rec',
                               name=get_user_data())
    return redirect(url_for('login'))


@app.route("/update_profile", methods=['GET', 'POST'])
def update_profile():
    msg = None
    if request.method == 'POST' and 'username' in session:
        if 'password' in request.form and 're_password' in request.form:
            if request.form['password'] == request.form['re_password']:
                if valid_login(session['username'], request.form['password']):
                    if 'username' in request.form and request.form['username'] != "":
                        if not execute_one_query("SELECT * FROM person WHERE username = %s", request.form['username']):
                            execute_one_query("UPDATE person SET username = %s WHERE username = %s",
                                              (request.form['username'], session['username']))
                            return log_the_user_in(request.form['username'])
                        else:
                            msg = "That username already exists"
                    elif 'email' in request.form and request.form['email'] != "":
                        if not execute_one_query("SELECT * FROM person WHERE email = %s", request.form['email']):
                            execute_one_query("UPDATE person SET email = %s WHERE username = %s",
                                              (request.form['email'], session['username']))
                        else:
                            msg = "That email is already registered"
                else:
                    msg = "Password's incorrect"
            else:
                msg = "Passwords don't match"
    if 'username' in session:
        return render_template("update_profile.html", page='update', name=get_user_data(), msg=msg)
    return redirect(url_for('login'))


@app.route('/myvideos', methods=['POST', 'GET'], defaults={'page': 1})
@app.route('/myvideos?page=<int:page>')
def myvideos(page):
    if request.method == 'POST':
        return redirect(url_for('home'))
    if 'username' in session:
        perpage = 12
        total_pages = int(np.ceil(np.asarray(execute_one_query("select count(*) from video"))[0] / perpage))
        startat = (page - 1) * perpage

        query = "SELECT title, uploadDate, idVideo FROM video WHERE username=%s ORDER BY uploadDate DESC LIMIT " + str(
            startat) + ", " + str(perpage)
        videos = np.asarray(
            execute_one_query(query,
                              session['username'], True))

        if len(videos) > 0:
            videos = np.hstack((videos, np.zeros((videos.shape[0], 1))))

            for v in videos:
                v[0] = urllib.parse.unquote(v[0])
                thumbnail = execute_one_query("SELECT imagePath FROM thumbnail WHERE idVideo=%s", v[2])
                if not thumbnail or not os.path.isfile(str(np.asarray(thumbnail)[0])):
                    v[3] = os.path.join(THUMBNAILS_DIRECTORY, "default-thumbnail.png")
                else:
                    v[3] = np.asarray(thumbnail)[0]

        return render_template('myvideos.html', page='myvideos', name=get_user_data(),
                               videos=tuple(videos), pagination=[page, total_pages])
    else:
        return redirect(url_for('login'))


@app.route('/import_video', methods=['GET', 'POST'])
def import_video():
    if request.method == 'POST':
        if 'upFile' in request.files:
            file = request.files['upFile']
            filename = urllib.parse.quote(secure_filename(file.filename))
            full_path = os.path.join(UPLOAD_DIRECTORY, filename)
            if os.path.exists(full_path):
                return jsonify({'msg': 'File already exists in the database', 'filenameimage': "", 'linkVideo': ""})
            if allowed_file(file.filename):
                recTime = None
                if 'datetimeRec' in request.form and request.form['datetimeRec'] != "":
                    recTime = str(request.form['datetimeRec']).replace("T", " ") + ":00"
                if 'dateRec' in request.form and request.form['dateRec'] != "":
                    date = request.form['dateRec']
                    if date != '' and datetime.strptime(date, "%d/%m/%Y").date() < datetime.today():
                        recTime = date if date != '' else None
                        if 'timeRec' in request.form:
                            timeR = request.form['timeRec']
                            if timeR != '':
                                recTime += recTime + timeR + ":00"
                            else:
                                recTime = date + "00:00:00"
                    else:
                        return jsonify(
                            {'msg': 'Future dates are not allowed', 'filenameimage': "", 'linkVideo': ""})
                location = None
                lat = ""
                lon = ""
                if 'latitude' in request.form:
                    lat = request.form['latitude']
                if 'longitude' in request.form:
                    lon = request.form['longitude']
                if lat != "" and lon != "":
                    location = lat + ';' + lon
                print('Saving')
                with open(os.path.join(UPLOAD_DIRECTORY, filename), "wb"):
                    file.save(os.path.join(UPLOAD_DIRECTORY, filename))
                thumbnail_path, id_video = insert_video_db(session['username'], file, filename, recTime, location,
                                                           request.form['title'])
                msg = "File successfully uploaded: " + file.filename
                return jsonify({'msg': msg, 'filenameimage': thumbnail_path,
                                'linkVideo': request.base_url.replace('import_video', 'after_recording') + "/" + str(
                                    id_video)})
        else:
            print('Redirecting')
            return redirect(url_for('import_video'))
    if 'username' in session:
        return render_template('import_video.html', page='importvideo', name=get_user_data(),
                               browser=request.user_agent.browser)
    else:
        return redirect(url_for('login'))


def allowed_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def insert_video_db(user: str, file, path: str, rec_time: str, location: str, titulo: str = None, id_video: int = None, 
                    is_to_create_thumbnail=True):
    if not titulo and file:
        titulo = secure_filename(file.filename)
    if not id_video:
        id_video = get_and_increment_current_video_id()
    video_path = os.path.join(UPLOAD_DIRECTORY, path)
    insert("INSERT INTO video values (%s, %s, %s, %s, %s, %s, %s)",
           [id_video, datetime.today().strftime('%Y-%m-%d %H:%M:%S'), titulo, user,
            video_path, rec_time, location])
    return create_thumbnail(video_path, id_video), id_video if is_to_create_thumbnail else None


def create_thumbnail(video_path: str, id_video: int) -> str:
    """ Call FFMPEG to create thumbnail and return its image path """
    filename = "th_" + str(id_video) + '.jpg'
    path = os.path.join(THUMBNAILS_DIRECTORY, filename)
    insert("INSERT INTO thumbnail VALUES (%s, %s)", [id_video, path])
    subprocess.call(
        ['ffmpeg', '-i', os.path.abspath(video_path), '-ss', '00:00:03.000', '-vframes', '1', path,
         "-y"])
    return path


def get_and_increment_current_video_id() -> int:
    id_video = execute_one_query("SELECT idVideo FROM currentVideoID")[0]
    execute_one_query("UPDATE projeto.currentvideoid set idVideo=idVideo+1")
    return id_video


def increment_current_annotation_id() -> None:
    execute_one_query("UPDATE projeto.currentannotationid set idAnnotation=idAnnotation+1")


def get_current_annotation_id() -> int:
    return execute_one_query("SELECT idAnnotation FROM currentAnnotationID")[0]


def get_and_increment_current_sensor_data_id() -> int:
    id_sdata = execute_one_query("SELECT idData FROM currentSensorDataID")[0]
    execute_one_query("UPDATE projeto.currentsensordataid set idData=idData+1")
    return id_sdata


@app.route('/after_recording/<idVideo>', methods=['POST', 'GET'])
def after_recording(idVideo):
    if request.method == 'POST':
        # todo changes (extra parameters) according to selected video
        return redirect(url_for('home'))
    if 'username' in session:
        author = execute_one_query(
            "SELECT username FROM video WHERE idVideo=%s", idVideo)
        if author and session['username'] == str(author[0]):
            session['idVideo'] = idVideo
            video = execute_one_query(
                "SELECT title, uploadDate, location, recTime, pathName FROM video WHERE username=%s AND idVideo=%s",
                [session['username'], idVideo])
            if not os.path.exists(video[4]):
                return make_response('Unavailable video', 400)
            
            if platform.system() == "Windows":
                path = pathlib.PureWindowsPath(r'' + str(video[4]))
                path = str(path.as_posix()).split("static/")[1]
                
            elif platform.system() == "Darwin":
                path = str(video[4]).split(os.path.join("static", ""))[1]
            
            return render_template('after_recording.html', page='pos_rec', name=get_user_data(),
                                   video=video, path=path)
        else:
            return make_response('Access forbidden', 403)
    else:
        return redirect(url_for('login'))


# ==================================
# ==== WEBSOCKET CONNECTIONS ====

# Handler for a message received over 'emotionButton' channel
@socketio.on('emotionButton')
def receive_emotion(message):
    print(message)
    print("clicked", message['type'])
    insert_emotion([message['type'], message['frameID'], session['idVideo'], message['duration']])


def insert_emotion(emotion_details) -> None:
    insert(
        "INSERT INTO videoAnnotation(emotionType, iniTime, idVideo, customText, duration) VALUES (%s, %s, %s, %s, %s)",
        [emotion_details[0], emotion_details[1], emotion_details[2], None, emotion_details[3]])
    increment_current_annotation_id()
    id_request_reply()

def insert_emotion(emotion_details) -> None:
    insert(
        "INSERT INTO videoAnnotation(emotionType, iniTime, idVideo, customText, duration) VALUES (%s, %s, %s, %s, %s)",
        [emotion_details[0], emotion_details[1], emotion_details[2], None, emotion_details[3]])
    increment_current_annotation_id()
    id_request_reply()


# Handler for a message received over 'customInput' channel
@socketio.on('customInput')
def receive_input(message):
    print("input", message['type'], message['data'])
    insert(
        "INSERT INTO videoAnnotation(emotionType, iniTime, idVideo, customText, duration) VALUES (%s, %s, %s, %s, %s)",
        [message['type'], message['frameID'], session['idVideo'], message['data'], None])
    increment_current_annotation_id()
    id_request_reply()


@socketio.on('deleteAnnotation')
def remove_annotation(message):
    print("removed", message['idAnnotation'])
    insert("DELETE FROM videoAnnotation WHERE idAnnotation = %s",
           message['idAnnotation'])


@socketio.on('editAnnotation')
def edit_annotation(message):
    print("edited", message['idAnnotation'], message['newValue'], message['newInitFrame'], message['newDuration'])
    all_annotations = np.asarray(
        execute_one_query("SELECT emotionType, emotion FROM annotation", fetchall=True))

    emotions = all_annotations[all_annotations[:, 1] == '1', 0]
    if message['newValue'] in emotions:
        execute_one_query(
            "UPDATE videoAnnotation SET emotionType=%s, iniTime=%s, duration=%s, customText=%s WHERE idAnnotation = %s",
            [message['newValue'], message['newInitFrame'], message['newDuration'], "",
             message['idAnnotation']])
    else:
        execute_one_query(
            "UPDATE videoAnnotation SET customText=%s, iniTime=%s, duration=%s, emotionType=%s WHERE idAnnotation = %s",
            [message['newValue'], message['newInitFrame'], message['newDuration'], "custom", message['idAnnotation']])


@socketio.on('saveChanges')
def save_annotations():
    print("saved annotations video: ", session['idVideo'])
    generate_json_range(session['idVideo'])
    socketio.emit("saved")


# Handler for a message received over 'my event' channel
@socketio.on('my event')
def connect_input(message):
    print("input", message['data'])


@socketio.on('ask for id')
def id_request_reply():
    socketio.emit("newID", {'id': get_current_annotation_id()})


@socketio.on('ask for json')
def json_request_reply():
    if 'idVideo' in session:
        json_path = os.path.join(JSON_DIRECTORY, "vid_an" + str(session['idVideo']) + ".json")
        if os.path.exists(json_path):
            file = open(json_path, 'r')
            json_file = json.load(file)  # else socketio.emit("annotations_json", "")
            file.close()
            socketio.emit("annotations_json", {'data': json_file})
    else:
        myvideos()


@socketio.on('start_recording')
def start_recording( _ ):
    global com_socket_handler
    com_socket_handler.start_recording()
    insert_video_db(session['username'], None, "video_" + str(session['idVideo']) + ".mp4", None, None, "", session['idVideo'], False)

# Handler for a message received over 'leaveRecording' channel
@socketio.on('leaveRecording')
def leave_recording():
    global com_socket_handler
    print("left Recording")
    # session.pop('idVideo', None)
    # com_socket_handler.close_socket()
    com_socket_handler = None


# Handler for a message received over 'deepface_start' channel
@socketio.on('deepface_start')
def call_deepface():
    """ Start a new Deepface analysis thread """
    if 'idVideo' in session and 'username' in session:
        id_vid = session['idVideo']
        user = session['username']
        df = DeepFaceClassifier(id_vid, str(
            np.asarray(execute_one_query("SELECT pathName FROM video WHERE username=%s AND idVideo=%s",
                                         [user, id_vid]))[0]), insert_emotion, socketio)
        df.start()


def generate_json_range(id_video: int):
    """ Generate and save the JSON annotations file """
    filename = "vid_an" + str(id_video)

    annotations = np.asarray(
        execute_one_query(
            "SELECT emotionType, idAnnotation, iniTime, duration, customText FROM videoAnnotation WHERE idVideo = %s ORDER BY idAnnotation DESC",
            id_video, True))

    signals = np.asarray(
        execute_one_query(
            "SELECT dataType, valueData, iniTime, duration FROM sensorData WHERE idVideo = %s", id_video, True))

    all_annotations = np.asarray(
        execute_one_query("SELECT emotionType, emotion FROM annotation", fetchall=True))

    # lists of every possible type of annotations
    emotions = all_annotations[all_annotations[:, 1] == '1', 0]
    custom = all_annotations[all_annotations[:, 1] == '2', 0]
    others = all_annotations[all_annotations[:, 1] == '3', 0]

    # json in dict format
    json_vid = {"video": id_video}

    emotions_arr = np.array([])
    custom_arr = np.array([])
    others_arr = np.array([])
    
    print(annotations)

    if annotations.size > 0:
        # lists of emotions, custom and other annotations for the current video
        bool_array_emotions = np.isin(annotations[:, 0], emotions)
        
        print(bool_array_emotions)
        
        emotions_arr = annotations[bool_array_emotions, 0:4]

        bool_array_custom = np.isin(annotations[:, 0], custom)
        custom_arr = annotations[bool_array_custom, 1:]

        # get last column to be the first
        custom_arr[:, [3, 0]] = custom_arr[:, [0, 3]]
        custom_arr[:, [3, 1]] = custom_arr[:, [1, 3]]
        custom_arr[:, [3, 2]] = custom_arr[:, [2, 3]]

        bool_array_others = np.isin(annotations[:, 0], others)
        others_arr = annotations[bool_array_others]

        for i in range(len(emotions_arr[:, 1])):
            emotions_arr[i, 1] = {"id": emotions_arr[i, 1]}

        for i in range(len(custom_arr[:, 1])):
            custom_arr[i, 1] = {"id": custom_arr[i, 1]}

    json_emotions = {"emotions": {"detected": list(emotions_arr.tolist()),
                                  "custom": list(custom_arr.tolist())},
                     "body_signals": list(signals.tolist()),
                     "others": list(others_arr.tolist())}

    json_vid['annotations'] = json_emotions
    json_vid["other_data"] = {}

    string_json = json.dumps(json_vid)
    
    print(json_vid)    
    print(string_json)
    
    with open(os.path.join(JSON_DIRECTORY, filename) + '.json', 'w') as f:
        f.write(string_json)
    return string_json


if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", debug=True, port=5000)
