from flask import Flask, render_template, request, redirect, url_for
import mysqlx
# from flask.ext.mysql import MySQL
from datetime import datetime

app = Flask(__name__)


# db = MySQL()

# MySQL configurations
# app.config['MYSQL_DATABASE_USER'] = 'jay'
# app.config['MYSQL_DATABASE_PASSWORD'] = 'jay'
# app.config['MYSQL_DATABASE_DB'] = 'BucketList'
# app.config['MYSQL_DATABASE_HOST'] = 'localhost'
# db.init_app(app)


@app.route("/", methods=['GET', 'POST'])
def home():
    print("hi4")
    if request.method == 'POST':
        print("hi5")
        # todo changes (extra parameters) according to recorded video
        return redirect(url_for('after_recording'))
    return render_template("page.html", page='on_rec')

    # class Todo(db.Model):
    # id = db.Column(db.Integer, primary_key=True)
    # content = db.Column(db.String(200), nullable=False)
    # date_created = db.Column(db.DateTime, default=datetime.utcnow)

    # def __repr__(self) -> str:
    #     return "<Task %r>" % self.id


@app.route('/myvideos', methods=['POST', 'GET'])
def myvideos():
    print("hi6")
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


@app.route('/stop_recording', methods=['GET'])
def stop_recording():
    print("hi, time to process what was recorded")
    return redirect(url_for('after_recording'))

if __name__ == "__main__":
    app.run(debug=True)
