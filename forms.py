from flask_ckeditor import CKEditorField
from wtforms import Form, BooleanField, StringField, PasswordField, validators
from wtforms.fields.simple import EmailField, SubmitField, URLField
from wtforms.validators import DataRequired, Length
from flask_wtf import FlaskForm


class RegisterForm(FlaskForm):
    name = StringField("Username: ", validators=[DataRequired(), Length(max=30)])
    email = EmailField("Email: ", validators=[DataRequired(), Length(max=30)])
    password = PasswordField("Password: ", validators=[DataRequired(), Length(min=4, max=30)])
    submit = SubmitField('Submit')

class LogIn(FlaskForm):
    email = EmailField("Email: ", validators=[DataRequired(), Length(max=30)])
    password = PasswordField("Password: ", validators=[DataRequired(), Length(min=4, max=30)])
    submit = SubmitField('Submit')


class PostForm(FlaskForm):

    title = StringField('Title', validators=[DataRequired()])
    subtitle = StringField('Subtitle', validators=[DataRequired()])
    # by = StringField('Your name:', validators=[DataRequired()])
    image_url = URLField('Image URL', validators=[DataRequired()])
    content = CKEditorField('Content', validators=[DataRequired()])
    submit = SubmitField('Submit')


class CommentForm(FlaskForm):
    content = CKEditorField('Comment', validators=[DataRequired(), Length(max=300)])
    submit = SubmitField('Submit')