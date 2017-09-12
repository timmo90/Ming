from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
	SelectField, TextAreaField
from wtforms import ValidationError
from wtforms.validators import Required, EqualTo, Email, Length, Regexp
from models import User, Role, Post, Comment
from flask_pagedown.fields import PageDownField 

class LoginForm(FlaskForm):
	email = StringField('Email', validators = [Required(), Length(1, 64), Email()])
	password = PasswordField('Password', validators = [Required()])
	remember_me = BooleanField('Keep me logged in')
	submit = SubmitField('Log In')


class RegisterForm(FlaskForm):
	email = StringField('Email', validators = [Required(), Length(1, 64), Email()])
	username = StringField('Username', validators = [Required(), 
		Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Username must have only letters,\
			numbers, dots and underscores')])
	password = PasswordField('Password', validators = [Required()])
	password_confirm = PasswordField('Password_confirm', validators = [Required(), 
		EqualTo('password', message = 'Password must match')])
	submit = SubmitField('Register')

	def validate_email(self, field):
		if User.query.filter_by(email = field.data).first():
			raise ValidationError('Email has already register, please login directly')

	def validate_username(self, field):
		if User.query.filter_by(username = field.data).first():
			raise ValidationError('Username has already register, please login directly')
		
class ChangePasswordForm(FlaskForm):
	old_password = StringField('Old Password', validators = [Required()])
	password = PasswordField('New Password', validators = [Required()])
	password_confirm = PasswordField('Password Confirm', validators = [Required(), 
		EqualTo('password', message = 'Password must match')])
	submit = SubmitField('ChangePassword')


class EditProfileForm(FlaskForm):
	name = StringField('Real name', validators = [Length(0, 64)])
	location = StringField('Location', validators = [Length(0, 64)])
	about_me = StringField('About me')
	submit = SubmitField('Submit')


class EditProfileAdminForm(FlaskForm):
	email = StringField('Email', validators = [Required(), Length(1, 64), Email()])
	username = StringField('Username', validators = [Required(), Length(1, 64),
		Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Username must have only letters,\
			numbers, dots, or underscores')])
	confirmed = BooleanField('Confirmed')
	role = SelectField('Role', coerce = int)
	name = StringField('Real name', validators = [Length(0, 64)])
	location = StringField('Location', validators = [Length(0, 64)])
	about_me = TextAreaField('About me')
	submit = SubmitField('Submit')

	def __init__(self, user, *args, **kwargs):
		super(EditProfileAdminForm, self).__init__(*args, **kwargs)
		self.role.choices = [(role.id, role.name) 
		for role in Role.query.order_by(Role.name).all()]
		self.user = user 

	def validate_email(self, field):
		if field.data != self.user.email and \
				User.query.filter_by(email = field.data).first():
			raise ValidationError('Email already registered.')

	def validate_username(self, field):
		if field.data != self.user.username and \
				User.query.filter_by(username = field.data).first():
			raise ValidationError('Username already in use.')
		

class PostForm(FlaskForm):
	body = PageDownField("What is in your mind?", validators = [Required()])
	submit = SubmitField('Submit')


class CommentForm(FlaskForm):
	body = StringField('Enter your comment', validators = [Required()])
	submit = SubmitField('Submit')
		
		
		
	
		
		