from functools import wraps
from flask_gravatar import Gravatar
from flask import Flask, render_template, request, url_for, flash, abort
import requests
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from flask_wtf import FlaskForm
from werkzeug.utils import redirect
from wtforms import StringField, TextAreaField, SubmitField, MultipleFileField, DateField, URLField
from wtforms.validators import DataRequired
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor, CKEditorField
from datetime import datetime
from forms import RegisterForm, PostForm, LogIn, CommentForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, UserMixin, logout_user, current_user



login_manager = LoginManager()

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
url_posts = "https://api.npoint.io/1ab87ffa3de8062770c7"
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"
# initialize the app with the extension
ckeditor = CKEditor(app)
db.init_app(app)
bootstrap = Bootstrap5(app)
app.config['SECRET_KEY'] = "1234"
class Posts(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[str] = mapped_column(nullable=True, default="unknow")
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    author = relationship("Users", back_populates="posts")
    title: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()
    subtitle: Mapped[str] = mapped_column()
    image_url: Mapped[str] = mapped_column()
    comments = relationship("Comments", back_populates="parent_post")


class Users(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    password: Mapped[str] = mapped_column()
    posts = relationship("Posts", back_populates="author")
    comments = relationship("Comments", back_populates="comment_author")

class Comments(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    comment_author = relationship("Users", back_populates="comments")
    post_id: Mapped[str] = mapped_column(Integer, db.ForeignKey("posts.id"))
    parent_post = relationship("Posts", back_populates="comments")

# response = requests.get(url_posts)
# response.raise_for_status()
# posts = response.json()["posts"]
with app.app_context():
    db.create_all()
    #
    # response = requests.get(url_posts)
    # data = response.json()['posts']
    # for post in data:
    #     print(post)
    #     new_post= Posts(
    #         id = post['id'],
    #         by = post['by'],
    #         date = post['date'],
    #         title = post['title'],
    #         content = post['content'],
    #         subtitle = post['subtitle'],
    #         image_url = post['image_url'],
    #     )
    #     db.session.add(new_post)
    # db.session.commit()

login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(Users, user_id)

@app.context_processor
def inject_year():
    return {'year': datetime.now().year}


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        try :
            current_user.id
        except AttributeError:
            return abort(403)
        else:
            if current_user.id != 1:
                return abort(403)
            #Otherwise continue with the route function
            return f(*args, **kwargs)
    return decorated_function

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

@app.route("/")
def home():
    posts = db.session.execute(db.select(Posts).order_by(Posts.id.desc())).scalars()
    return render_template("index.html", all_posts=posts)

@app.route('/new-post', methods=['POST', 'GET'])
@admin_only
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        new_post = Posts(
                author_id = current_user.id,
                date = datetime.now().strftime("%B %d, %Y"),
                title = form.title.data,
                content = form.content.data,
                subtitle = form.subtitle.data,
                image_url = form.image_url.data,
            )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('make-post.html', form=form, header='New post')

@admin_only
@app.route("/edit-post/<post_id>", methods=['GET', 'POST'])
def edit_post(post_id):
    the_post = db.get_or_404(Posts, post_id)
    form = PostForm(
        title=the_post.title,
        subtitle = the_post.subtitle,
        by = the_post.by,
        image_url = the_post.image_url,
        content = the_post.content,

    )
    if form.validate_on_submit():
        the_post.by = form.by.data
        # the_post.date = datetime.now().strftime("%B %d, %Y")
        the_post.title = form.title.data
        the_post.content = form.content.data
        the_post.subtitle = form.subtitle.data
        the_post.image_url = form.image_url.data
        db.session.commit()
        return redirect(url_for("post", num=the_post.id))
    return render_template('make-post.html', header='Edit post', form=form)

@app.route("/post/<int:num>", methods=['POST', 'GET'])
def post(num):
    requested_post = db.get_or_404(Posts, num)
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

        new_comment = Comments(
            text=comment_form.content.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
    return render_template("post.html", post=requested_post, comment=comment_form)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=['POST', 'GET'])
def contact():
    if request.method == "POST":
        name =request.form['name']
        email =request.form['email']
        phone =request.form['phone']
        message =request.form['msg']
        with open("message.txt", 'a') as file:
            #this can be email
            file.write(f"{name}, {email}, {phone}, {message} \n")
        return render_template("contact.html", header="Successfully sent message")
    else:
        return render_template("contact.html", header="Contact Me")


@app.route("/contact", methods=['POST'])
def receive_data():
    print(request.form['name'], request.form['email'], request.form['phone'], request.form['msg'])
    return render_template("contact.html", header="Successfully sent message")

@app.route("/delete/<post_id>")
@admin_only
def delete(post_id):
    the_post = db.get_or_404(Posts, post_id)
    db.session.delete(the_post)
    db.session.commit()
    return redirect(url_for('home'))
@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        new_user = Users(
            name= form.name.data,
            email = form.email.data,
            password = generate_password_hash(form.password.data, method='pbkdf2', salt_length=16)
        )
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            flash("this email already registered")
            return redirect(url_for("login"))
        else:
            login_user(new_user)
            return redirect(url_for('home'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LogIn()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        try:
            user = db.session.execute(db.select(Users).filter_by(email=email)).scalar_one()
        except NoResultFound:
            flash('Wrong email')
        else:
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash('Wrong password')

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))



if __name__ == "__main__":
    app.run(debug=True, port=5001)