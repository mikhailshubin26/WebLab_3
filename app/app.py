import random
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

from flask import (
    Flask,
    render_template,
    session,
    request,
    redirect,
    url_for,
    flash
)
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from faker import Faker
from werkzeug.security import generate_password_hash, check_password_hash


fake = Faker()
load_dotenv()

app = Flask(__name__)
application = app
app.config["SECRET_KEY"] = os.getenv("FLASK_KEY")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Для доступа к запрашиваемой странице необходимо пройти аутентификацию."
login_manager.login_message_category = "warning"

images_ids = [
    '7d4e9175-95ea-4c5f-8be5-92a6b708bb3c',
    '2d2ab7df-cdbc-48a8-a936-35bba702def5',
    '6e12f3de-d5fd-4ebb-855b-8cbc485278b7',
    'afc2cfe7-5cac-4b80-9b9a-d5c65ef0c728',
    'cab5b7f2-774e-4884-a200-0c0180fa777f'
]


def generate_comments(replies=True):
    comments = []
    for _ in range(random.randint(1, 3)):
        comment = {
            "author": fake.name(),
            "text": fake.text()
        }
        if replies:
            comment["replies"] = generate_comments(replies=False)
        comments.append(comment)
    return comments


def generate_post(i):
    return {
        "title": "Заголовок поста",
        "text": fake.paragraph(nb_sentences=100),
        "author": fake.name(),
        "date": fake.date_time_between(start_date="-2y", end_date="now"),
        "image_id": f"{images_ids[i]}.jpg",
        "comments": generate_comments()
    }


posts_list = sorted(
    [generate_post(i) for i in range(5)],
    key=lambda p: p["date"],
    reverse=True
)


class User(UserMixin):
    def __init__(self, user_id, login, password_hash):
        self.id = user_id
        self.login = login
        self.password_hash = password_hash


users = {
    "user": User(
        user_id="1",
        login="user",
        password_hash=generate_password_hash("qwerty")
    )
}


@login_manager.user_loader
def load_user(user_id):
    for user in users.values():
        if user.id == user_id:
            return user
    return None


def is_safe_url(target):
    if not target:
        return False

    ref_url = urlparse(request.host_url)
    test_url = urlparse(urlparse(request.host_url)._replace(path=target).geturl()
                        if target.startswith("/")
                        else target)

    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


@app.route("/")
def index():
    return render_template("index.html", title="Главная")


@app.route("/counter")
def counter():
    session["visits_count"] = session.get("visits_count", 0) + 1
    return render_template(
        "counter.html",
        title="Счётчик посещений",
        visits=session["visits_count"]
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        flash("Вы уже вошли в систему.", "info")
        return redirect(url_for("index"))

    if request.method == "POST":
        login_value = request.form.get("login", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = users.get(login_value)

        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            flash("Вход выполнен успешно.", "success")

            next_page = request.args.get("next")
            if next_page and is_safe_url(next_page):
                return redirect(next_page)

            return redirect(url_for("index"))

        flash("Неверный логин или пароль.", "danger")

    return render_template("login.html", title="Вход")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта.", "info")
    return redirect(url_for("index"))


@app.route("/secret")
@login_required
def secret():
    return render_template("secret.html", title="Секретная страница")


@app.route("/posts")
def posts():
    return render_template("posts.html", title="Посты", posts=posts_list)


@app.route("/posts/<int:index>")
def post(index):
    p = posts_list[index]
    return render_template("post.html", title=p["title"], post=p)


@app.route("/about")
def about():
    return render_template("about.html", title="Об авторе")


if __name__ == "__main__":
    app.run(debug=True)