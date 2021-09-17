import mimetypes
import re
import secrets
from time import time
from urllib.parse import urlparse, urljoin
import os
from zlib import adler32

import flask
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, make_response, session, Response, \
    stream_with_context, send_from_directory, send_file, copy_current_request_context
from flaskext.mysql import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO
from zmq.utils.strtypes import unicode
import subprocess
from send_frame_handler import SendFrame
from os import rename

# =======================================
from datetime import datetime
import urllib
import json


UPLOAD_DIRECTORY = "./static/videos"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

ALLOWED_EXTENSIONS = {'mpeg', 'mp4'}
# ==================================
# ==== APP INITIALIZATION PARAMETERS ====
app = Flask(__name__)
app.secret_key = secrets.token_bytes(16)

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
# app.config['MYSQL_DATABASE_PASSWORD'] = 'QueroPote2026*'
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

# ==================================
# ==== SERVER AUXILIARY OBJECTS ====
com_socket_handler = None
videos_dir_path = "static/videos/"


# ==================================
# ==== DATABASE FUNCTIONS ====


def get_cursor_db():
    db_con.autocommit(True)
    return db_con.cursor()


def execute_one_query(query, params=None, fetchall=False):
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
        print("Problem inserting into db: " + str(e))
        return False
    return result


def insert(query, params=None):
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


def log_the_user_in(username):
    session['username'] = username
    # admin = execute_one_query("SELECT adm FROM person WHERE username = %s", username)
    return redirect(url_for('myvideos'))


def valid_login(username, password):
    # db fetching
    account = execute_one_query("SELECT * FROM person WHERE username = %s", username)
    if account:
        # if check_password_hash(account[1], password):
        if check_password_hash(account[1], password):
            return True
    return False


def get_user_data(username):
    # db fetching
    return session['username'], execute_one_query("SELECT email FROM person WHERE username = %s", username)[0]


# ==================================
# ==== LOGOUT METHOD ====


@app.route('/logout')
def logout():
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
            if len(request.form['pass']) < 6:
                error = 'Password must have 6 ou more characters'
        # the code below is executed if the request method
        # was GET or the credentials were invalid
    return render_template('signup.html', page='signup', error=error)


def valid_registration(email, username):
    # query db
    account = execute_one_query("SELECT * FROM person WHERE email = %s OR username = %s", [email, username])
    if account:
        return False
    elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
        return False
    elif not re.match(r'[A-Za-z0-9]+', username):
        return False
    return True


def register_user(username, password, email):
    # insert db
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

# def _convert_image_to_jpeg(frame):
#     ret, buffer = cv2.imencode('.jpg', frame)
#     frame = buffer.tobytes()
#     return (b'--frame\r\n'
#             b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result


# def generate(debug=False):
#     print("VIDEO")
#     if debug:
#         cam = cv2.VideoCapture(0)
#         while True:
#             flag, frame = cam.read()
#             ret, buffer = cv2.imencode('.jpg', frame)
#             frame = buffer.tobytes()
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
#     else:
#         global com_socket_handler
#         if len(com_socket_handler.get_buffer) != 0:
#             print("yes")
#             frame = _convert_image_to_jpeg(com_socket_handler.get_buffer.pop())
#         else:
#             frame = cv2.imread("./static/imgs/eyeLogo.png")
#             frame = _convert_image_to_jpeg(cv2.resize(frame, (640, 480)))
#             print("no")
#         print(type(frame))
#         return frame

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
        vid_title = request.form['vid_title']
        # todo fetch & store extra parameters according to recorded video
        print("title", vid_title)
        
        if vid_title:
            rename(videos_dir_path + "teste.avi", videos_dir_path + vid_title + ".avi")
        
        return redirect(url_for('after_recording'))
    
    if 'username' in session:
        if not com_socket_handler:
            com_socket_handler = SendFrame(socketio)
            com_socket_handler.daemon = False
            com_socket_handler.start()
        
        recTime = ""
        location = ""
        video_file = None
        generate_json(session['idVideo'])
        insert_video_db(session['username'], video_file, recTime, location, vid_title)
        return redirect(url_for('after_recording', idVideo=session['idVideo']))
    if 'username' in session:
        if not com_socket_handler:
            com_socket_handler = SendFrame()
            com_socket_handler.start()
        session['idVideo'] = get_and_increment_current_video_id()
        return render_template("page.html", page='on_rec', name=get_user_data(
            session['username']))
        
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
        return render_template("update_profile.html", page='update', name=get_user_data(session['username']), msg=msg)
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
            filename = urllib.parse.quote(file.filename)
            full_path = os.path.join(UPLOAD_DIRECTORY, filename)
            if os.path.exists(full_path):
                return make_response(('File already exists', 400))
            if allowed_file(file.filename):
                with open(os.path.join(UPLOAD_DIRECTORY, filename), "wb") as fp:
                    file.save(os.path.join(UPLOAD_DIRECTORY, filename))
                    recTime = None
                    location = None
                    insert_video_db(session['username'], file, recTime, location)
                    # Return 201 CREATED
                    return redirect('myvideos', 201)
        else:
            redirect(url_for('importvideo'))
    if 'username' in session:
        return render_template('import_video.html', page='importvideo', name=get_user_data(session['username']))
    else:
        return redirect(url_for('login'))


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def insert_video_db(user, file, rec_time, location, titulo=None):
    if not titulo:
        titulo = file.filename
    video_path = os.path.join(UPLOAD_DIRECTORY, urllib.parse.quote(file.filename))
    id_video = get_and_increment_current_video_id()
    insert("INSERT INTO video values (%s, %s, %s, %s, %s, %s, %s)",
           [id_video, datetime.today().strftime('%Y-%m-%d-%H:%M:%S'), titulo, user,
            video_path, rec_time, location])
    create_thumbnail(video_path, id_video)


def create_thumbnail(video_path, id_video):
    filename = "th_" + str(id_video) + '.jpg'
    path = os.path.join(UPLOAD_DIRECTORY, "thumbnails", filename)
    insert("INSERT INTO thumbnail VALUES (%s, %s)", [id_video, path])
    subprocess.call(
        ['ffmpeg', '-i', os.path.abspath(video_path), '-ss', '00:00:03.000', '-vframes', '1', path,
         "-y"])


def get_and_increment_current_video_id():
    id_video = execute_one_query("SELECT * FROM currentVideoID")[0]
    execute_one_query("UPDATE projeto.currentvideoid set idVideo=idVideo+1")
    return id_video


@app.route('/after_recording/<idVideo>', methods=['POST', 'GET'])
def after_recording(idVideo):
    if request.method == 'POST':
        # todo changes (extra parameters) according to selected video
        return redirect(url_for('home'))
    if 'username' in session:
        video = execute_one_query(
            "SELECT title, uploadDate, location, recTime, pathName FROM video WHERE username=%s AND idVideo=%s",
            [session['username'], idVideo])
        return render_template('after_recording.html', page='pos_rec', name=get_user_data(session['username']),
                               video=video, idV=idVideo)
    else:
        return redirect(url_for('login'))


def send_file_partial(path):
    """
        Simple wrapper around send_file which handles HTTP 206 Partial Content
        (byte ranges)
        (if it has any)
    """

    range_header = request.headers.get('Range', None)
    if not range_header:
        return send_file(path)

    size = os.path.getsize(os.path.abspath(path))
    byte1, byte2 = 0, None

    m = re.search('(\d+)-(\d*)', range_header)
    g = m.groups()

    if g[0]:
        byte1 = int(g[0])
    if g[1]:
        byte2 = int(g[1])

    length = size - byte1
    if byte2 is not None:
        length = byte2 - byte1 + 1

    with open(path, 'rb') as f:
        f.seek(byte1)
        data = f.read(length)

    rv = Response(data,
                  206,
                  mimetype=mimetypes.guess_type(path)[0],
                  direct_passthrough=True)
    rv.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(byte1, byte1 + length, size))
    rv.set_etag('flask-%s-%s-%s' % (
        os.path.getmtime(path),
        os.path.getsize(path),
        adler32(
            path.encode('utf8') if isinstance(path, unicode)
            else path
        ) & 0xffffffff
    ))
    rv.headers.add('Cache-Control', 'no-cache')
    return rv


@app.route('/get_video/<idVideo>', methods=['GET'])
def get_video(idVideo):
    path, name = execute_one_query("SELECT pathName, title FROM video WHERE username=%s AND idVideo=%s",
                                   [session['username'], idVideo])
    return send_file_partial(path)


# ==================================
# ==== WEBSOCKET CONNECTIONS ====

# Handler for a message received over 'emotionButton' channel
@socketio.on('emotionButton')
def receive_emotion(message):
    print("clicked", message['type'])
    insert("INSERT INTO videoAnnotation VALUES (%s, %s, %s, %s, %s)",
           [message['type'], message['frameID'], session['idVideo'], None, None])


# Handler for a message received over 'customInput' channel
@socketio.on('customInput')
def receive_input(message):
    print("input", message['type'], message['data'])

    insert("INSERT INTO videoAnnotation VALUES (%s, %s, %s, %s, %s)",
           [message['type'], message['frameID'], session['idVideo'], message['data'], None])


# Handler for a message received over 'my event' channel
@socketio.on('my event')
def connect_input(message):
    print("input", message['data'])
    
@socketio.on('stop_recording')
def end_connection( _ ):
    global com_socket_handler
    print(com_socket_handler)
    com_socket_handler.close_socket()
    com_socket_handler.join()
    com_socket_handler = None

@socketio.on('start_recording')
def start_recording( _ ):
    global com_socket_handler
    com_socket_handler.start_recording()


# if __name__ == "__main__":    
        
#     socketio.run(app, debug=True, port=5001)
#     if com_socket_handler:
#         com_socket_handler.close_socket()
#         com_socket_handler.join()


# Handler for a message received over 'leaveRecording' channel
@socketio.on('leaveRecording')
def leave_recording():
    global com_socket_handler
    print("left Recording")
    # session.pop('idVideo', None)
    # com_socket_handler.close_socket()


def generate_json(id_video):
    filename = "vid_an" + str(id_video)

    annotations = np.asarray(
        execute_one_query("SELECT emotionType, idFrame, customText FROM videoAnnotation WHERE idVideo = %s", id_video,
                          True))

    all_annotations = np.asarray(
        execute_one_query("SELECT emotionType, emotion FROM annotation", fetchall=True))

    emotions = all_annotations[all_annotations[:, 1] == '1', 0]

    frames = np.unique(annotations[:, 1])
    print("frames", frames)
    json_vid = {"video": id_video}

    for f in frames:
        frame_annot = annotations[annotations[:, 1] == f]

        bool_array_emotions = np.isin(frame_annot[:, 0], emotions)
        emotions = frame_annot[bool_array_emotions, 0]
        others = frame_annot[~bool_array_emotions]

        body_signs = {}
        if "heartbeat" in others:
            body_signs["heartbeat"] = int(others[others[:, 0] == "heartbeat", 2])
        if "sweat" in others:
            body_signs["sweat"] = int(others[others[:, 0] == "sweat", 2])

        manual = []
        if "manual" in emotions:
            manual = [others[others[:, 0] == "custom", 2][0]]

        other_annot = {}

        json_emotions = {"emotions": {"detected": list(emotions),
                                      "manual": manual},
                         "body_signs": body_signs,
                         "others": other_annot}
        # json_frame = {"frame": f, "annotations": json_emotions}
        json_vid["frame_" + str(f)] = {"annotations": json_emotions}

    json_vid["other_data"] = {}
    string_json = json.dumps(json_vid)
    with open(os.path.join(UPLOAD_DIRECTORY, "json", filename) + '.json', 'w') as f:
        f.write(string_json)
    return string_json


if __name__ == "__main__":
    socketio.run(app, debug=True, port=5001)
    # socketio.run(app, debug=True, port=5003)
    if com_socket_handler:
        com_socket_handler.close_socket()
        com_socket_handler.join()
