import secrets

from flask import Flask, render_template, request, redirect, url_for, make_response, session
import mysqlx
# from flask.ext.mysql import MySQL
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_bytes(16)


# db = MySQL()

# MySQL configurations
# app.config['MYSQL_DATABASE_USER'] = 'jay'
# app.config['MYSQL_DATABASE_PASSWORD'] = 'jay'
# app.config['MYSQL_DATABASE_DB'] = 'BucketList'
# app.config['MYSQL_DATABASE_HOST'] = 'localhost'
# db.init_app(app)


@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        if valid_login(request.form['your_name'],
                       request.form['your_pass']):
            return log_the_user_in(request.form['your_name'])
        elif request.form['your_pass'] is not "":
            error = 'Invalid username/password'

    # the code below is executed if the request method
    # was GET or the credentials were invalid

    return render_template('login.html', page='login', error=error)


def log_the_user_in(username):
    session['username'] = username
    return redirect(url_for('home'))


def valid_login(username, password):
    # db fetching
    return


def get_user_data(username):
    session['username'] = username
    # db fetching
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    error = None
    if request.method == 'POST':
        if request.form['pass'] == request.form['re_pass']:
            if valid_registration(request.form['email']):
                return register_user(request.form['name'],
                                     request.form['pass'], request.form['email'])
            else:
                error = 'That e-mail is already registered'
        elif request.form['pass'] is not "":
            error = 'Passwords don\'t match'
        if len(request.form['pass']) < 6:
            error = 'Password must have 6 ou more characters'
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return render_template('signup.html', page='signup', error=error)


def valid_registration(email):
    # query db
    return


def register_user(name, password, email):
    # insert db
    return


@app.route("/", methods=['GET', 'POST'])
def home():
    # if 'username' in session:
        # username = request.cookies.get('username')
    if request.method == 'POST':
            # todo changes (extra parameters) according to recorded video
        return redirect(url_for('after_recording'))
    return render_template("page.html", page='on_rec', name='Yay')  # get_user_data(session['username']))

    # class Todo(db.Model):
    # id = db.Column(db.Integer, primary_key=True)
    # content = db.Column(db.String(200), nullable=False)
    # date_created = db.Column(db.DateTime, default=datetime.utcnow)

    # def __repr__(self) -> str:
    #     return "<Task %r>" % self.id


@app.route('/myvideos', methods=['POST', 'GET'])
def myvideos():
    if request.method == 'POST':
        # todo changes (extra parameters) according to selected video
        return redirect(url_for('home'))
    return render_template('myvideos.html', page='myvideos')


@app.route('/after_recording', methods=['POST', 'GET'])
def after_recording():
    if request.method == 'POST':
        # todo changes (extra parameters) according to selected video
        return redirect(url_for('home'))
    return render_template('after_recording.html', page='pos_rec')


if __name__ == "__main__":
    app.run(debug=True)
