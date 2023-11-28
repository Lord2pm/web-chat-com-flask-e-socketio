from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy_serializer import SerializerMixin


app = Flask(__name__)
app.config["SECRET_KEY"] = "1234567890"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///chat.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
io = SocketIO(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Message(db.Model, SerializerMixin):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    user_name = db.Column(db.String(256), nullable=False)
    password = db.Column(db.Text, nullable=False)

    def __init__(self, message, user_name, password) -> None:
        self.message = message
        self.user_name = user_name
        self.password = password

    def __repr__(self) -> str:
        return self.message


@app.route("/")
def index():
    if "username" in session.keys():
        return render_template("index.html", username=session["username"], password=session["password"])

    return render_template("index.html")


@app.route("/sair")
def sair():
    session["username"] = None
    session["password"] = None

    return redirect(url_for("index"))


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    session["username"] = username
    session["password"] = password

    return redirect(url_for("index"))


@io.on("connect")
def hendler_connect():
    result = Message.query.all()

    print("Client connected")

    for row in result:
        msg = row.to_dict()
        emit("getMessages", {"msg": msg}, broadcast=False)


@io.on("sendMessage")
def hendler_user_join(data):
    message = Message(data["msg"], data["username"], data["password"])

    db.session.add(message)
    db.session.commit()

    emit("chat", {"msg": data}, broadcast=True)


if __name__ == "__main__":
    io.run(app, debug=True)
