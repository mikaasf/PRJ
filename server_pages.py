import re
import secrets
from urllib.parse import urlparse, urljoin

import cv2
import flask
from flask import Flask, render_template, request, redirect, url_for, make_response, session, Response, \
    stream_with_context
from flaskext.mysql import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit
from send_frame_handler import SendFrame


UPLOAD_DIRECTORY = "./videos"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

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
app.config['MAX_CONTENT_LENGTH'] = 256 * 1024 * 1024 # 256 mb


db = MySQL()
db.init_app(app)
db_con = db.connect()

socketio = SocketIO(app, cors_allowed_origins="*")
com_socket_handler = None


# ==================================
# ==== DATABASE FUNTIONS ====


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
                    error = 'That e-mail or username are already registered'
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


def _convert_image_to_jpeg(frame):
    ret, buffer = cv2.imencode('.jpg', frame)
    frame = buffer.tobytes()
    return (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result


def generate(debug=False):
    print("VIDEO")
    if debug:
        cam = cv2.VideoCapture(0)
        while True:
            flag, frame = cam.read()
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    else:
        global com_socket_handler
        if len(com_socket_handler.get_buffer) != 0:
            print("yes")
            frame = _convert_image_to_jpeg(com_socket_handler.get_buffer.pop())
        else:
            frame = cv2.imread("./static/imgs/eyeLogo.png")
            frame = _convert_image_to_jpeg(cv2.resize(frame, (640, 480)))
            print("no")
        print(type(frame))
        return frame


@app.route("/", methods=['GET', 'POST'])
def home():
    global com_socket_handler
    if request.method == 'POST':
        vid_title = request.form['vid_title']
        # todo fetch & store extra parameters according to recorded video
        print("title", vid_title)
        return redirect(url_for('after_recording'))
    if 'username' in session:
        if not com_socket_handler:
            com_socket_handler = SendFrame(socketio)
            com_socket_handler.daemon = True
            com_socket_handler.start()
        return render_template("page.html", page='on_rec', name=get_user_data(
            session['username']))  # , img_test=_convert_image_to_jpeg(cv2.resize(img, (640, 480))))

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


@app.route('/myvideos', methods=['POST', 'GET'])
def myvideos():
    if request.method == 'POST':
        return redirect(url_for('home'))
    if 'username' in session:
        videos = execute_one_query("SELECT title, uploadDate, idVideo FROM video WHERE username=%s", session['username'], True)
        return render_template('myvideos.html', page='myvideos', name=get_user_data(session['username']), videos=videos)
    else:
        return redirect(url_for('login'))


@app.route('/import_video', methods=['GET', 'POST'])
def import_video():
    if request.method == 'POST':
        if 'upFile' in request.files:
            file = request.files['upFile']
            if allowed_file(file.filename):
                with open(os.path.join(UPLOAD_DIRECTORY, file.filename), "wb") as fp:
                    fp.write(request.data)
                    recTime = None
                    location = None
                    insert("INSERT INTO video values (%s, %s, %s, %s, %s, %s, %s)",
                           [None, datetime.today().strftime('%Y-%m-%d-%H:%M:%S'), file.filename, session['username'], UPLOAD_DIRECTORY + "/" + file.filename, recTime, location])
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


@app.route('/after_recording/<idVideo>', methods=['POST', 'GET'])
def after_recording(idVideo):
    if request.method == 'POST':
        # todo changes (extra parameters) according to selected video
        return redirect(url_for('home'))
    if 'username' in session:
        video = execute_one_query("SELECT title, uploadDate, location, recTime FROM video WHERE username=%s AND idVideo=%s", [session['username'], idVideo])
        # todo load video from path, etc.
        return render_template('after_recording.html', page='pos_rec', name=get_user_data(session['username']), video=video, idV=idVideo)
    else:
        return redirect(url_for('login'))


CHUNK_SIZE = 8192
def read_file_chunks(path):
    with open(path, 'rb') as fd:
        while 1:
            buf = fd.read(CHUNK_SIZE)
            if buf:
                yield buf
            else:
                break


# fixme, not working yet
@app.route('/download_video/<idVideo>')
def download_video(idVideo):
    path, name = execute_one_query("SELECT pathName, title FROM video WHERE username=%s AND idVideo=%s", [session['username'], idVideo])
    if os.path.exists(path):
        return Response(
            stream_with_context(read_file_chunks(path)), mimetype="video/*", direct_passthrough=True
        )
    else:
        print("File Not Found")


# ==================================
# ==== WEBSOCKET CONNECTIONS ====


# Handler for a message recieved over 'emotionButton' channel
@socketio.on('emotionButton')
def receive_emotion(message):
    print("clicked", message['type'])
    # insert("INSERT INTO videoAnnotation VALUES (%s, %s, %s)", [message['type'], message['frameID'], message['videoID']]);


# Handler for a message recieved over 'customInput' channel
@socketio.on('customInput')
def receive_input(message):
    print("input", message['type'], message['data'])
    # insert("INSERT INTO videoAnnotation VALUES (%s, %s, %s)", [message['type'], message['frameID'], message['videoID'], message['data']]);


# Handler for a message recieved over 'connect' channel
@socketio.on('my event')
def connect_input(message):
    print("input", message['data'])


if __name__ == "__main__":    
        
    socketio.run(app, debug=False, port=5001)
