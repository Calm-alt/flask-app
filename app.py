import os
import secrets
from PIL import Image

from sqlalchemy import or_

from flask import (
    Flask,
    render_template,
    url_for,
    flash,
    redirect,
    request,
)

from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)

from forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm
from models import db, User, Post

app = Flask(__name__)

# ---------------- CONFIG ----------------

app.config["SECRET_KEY"] = "your_secret_key_here"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ---------------- DATABASE ----------------

db.init_app(app)

# ---------------- LOGIN MANAGER ----------------

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---------------- IMAGE SAVE FUNCTION ----------------

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext

    picture_path = os.path.join(
        app.root_path,
        "static/profile_pics",
        picture_fn
    )

    output_size = (125, 125)
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    img.save(picture_path)

    return picture_fn

# ---------------- HOME ----------------

@app.route("/")
@app.route("/home")
def home():
    page = request.args.get("page", 1, type=int)
    sort = request.args.get("sort", "latest")
    q = request.args.get("q", "").strip()

    query = Post.query

    # Search by title or content
    if q:
        query = query.filter(
            or_(
                Post.title.ilike(f"%{q}%"),
                Post.content.ilike(f"%{q}%")
            )
        )

    # Sorting
    if sort == "oldest":
        query = query.order_by(Post.date_posted.asc())
    else:
        query = query.order_by(Post.date_posted.desc())

    posts = query.paginate(
        page=page,
        per_page=5,
        error_out=False
    )

    return render_template(
        "home.html",
        posts=posts,
        sort=sort,
        q=q
    )
# ---------------- ABOUT ----------------

@app.route("/about")
def about():
    return render_template("about.html", title="About")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = RegistrationForm()

    if form.validate_on_submit():

        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for("login"))

        if User.query.filter_by(username=form.username.data).first():
            flash("Username already exists.", "warning")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(form.password.data)

        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully!", "success")
        return redirect(url_for("login"))

    return render_template("register.html", title="Register", form=form)


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = LoginForm()

    if form.validate_on_submit():

        user = User.query.filter_by(email=form.email.data).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)

            flash(f"Welcome back, {user.username}!", "success")

            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("home"))

        flash("Login unsuccessful. Please check email and password.", "danger")

    return render_template("login.html", title="Login", form=form)


# ---------------- LOGOUT ----------------

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


# ---------------- ACCOUNT ----------------

@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = UpdateAccountForm()

    if form.validate_on_submit():

        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file

        current_user.username = form.username.data
        current_user.email = form.email.data

        db.session.commit()

        flash("Account updated successfully!", "success")
        return redirect(url_for("account"))

    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email

    image_file = url_for(
        "static",
        filename="profile_pics/" + (current_user.image_file or "default.jpg")
    )

    return render_template(
        "account.html",
        title="Account",
        image_file=image_file,
        form=form
    )


# ---------------- CREATE POST ----------------

@app.route("/post/new", methods=["GET", "POST"])
@login_required
def new_post():

    form = PostForm()

    if form.validate_on_submit():

        post = Post(
            title=form.title.data,
            content=form.content.data,
            author=current_user
        )

        db.session.add(post)
        db.session.commit()

        flash("Post created successfully!", "success")
        return redirect(url_for("home"))

    return render_template("create_post.html", title="New Post", form=form)


# ---------------- VIEW SINGLE POST ----------------

@app.route("/post/<int:post_id>")
def post(post_id):
    post = db.session.get(Post, post_id)

    if not post:
        flash("Post not found.", "warning")
        return redirect(url_for("home"))

    return render_template("post.html", title=post.title, post=post)


# ---------------- EDIT POST ----------------

@app.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = db.session.get(Post, post_id)

    if not post:
        flash("Post not found.", "warning")
        return redirect(url_for("home"))

    if post.author != current_user:
        flash("You are not allowed to edit this post.", "danger")
        return redirect(url_for("home"))

    form = PostForm()

    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()

        flash("Post updated successfully!", "success")
        return redirect(url_for("post", post_id=post.id))

    elif request.method == "GET":
        form.title.data = post.title
        form.content.data = post.content

    return render_template("create_post.html", title="Edit Post", form=form)


# ---------------- DELETE POST ----------------

@app.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = db.session.get(Post, post_id)

    if not post:
        flash("Post not found.", "warning")
        return redirect(url_for("home"))

    if post.author != current_user:
        flash("You are not allowed to delete this post.", "danger")
        return redirect(url_for("home"))

    db.session.delete(post)
    db.session.commit()

    flash("Post deleted successfully!", "success")
    return redirect(url_for("home"))


# ---------------- USER PROFILE ----------------

@app.route("/user/<string:username>")
def user_posts(username):
    user = User.query.filter_by(username=username).first_or_404()

    posts = (
        Post.query
        .filter_by(user_id=user.id)
        .order_by(Post.date_posted.desc())
        .all()
    )

    return render_template(
        "user_posts.html",
        title=f"{user.username}'s Profile",
        user=user,
        posts=posts
    )


# ---------------- RESET PASSWORD ----------------

@app.route("/reset_password")
def reset_request():
    return render_template("reset_request.html", title="Reset Password")


# ---------------- DB INIT ----------------

with app.app_context():
    db.create_all()

with app.app_context():
    db.drop_all()
    db.create_all()

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)