# -*- coding: utf-8 -*-

from flask import Flask, render_template, redirect, url_for, flash, abort,\
	request
from flask_bootstrap import Bootstrap 
import config
from flask_moment import Moment
from flask_pagedown import PageDown 
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, current_user, login_required, logout_user


app = Flask(__name__)
app.config.from_object(config)

db = SQLAlchemy(app)
bootstrap = Bootstrap(app)
login_manager = LoginManager(app)
moment = Moment(app)
pagedown = PageDown(app)

login_manager.session_protection = 'strong'
login_manager.login_view = 'login'



from models import Permission, User, Role, Post, Comment
from decorators import admin_required, permission_required
from forms import LoginForm, RegisterForm, ChangePasswordForm, \
	EditProfileForm, EditProfileAdminForm, PostForm, CommentForm

# @app.before_request
# def before_request():
# 	if current_user:
# 		current_user.ping()

@app.route('/', methods = ['GET', 'POST'])
def index():
	# Post.generate_fake(50)
	form = PostForm()
	if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
		post = Post(body = form.body.data,
			author = current_user._get_current_object())
		db.session.add(post)
		return redirect(url_for('index'))
	page = request.args.get('page', 1, type = int)
	pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
		page, per_page = config.MING_POSTS_PER_PAGE, error_out = False)
	posts = pagination.items
	return render_template('index.html', form = form, posts = posts,
		Permission = Permission, pagination = pagination)

@app.route('/login', methods = ['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email = form.email.data).first()
		if user is not None and user.verify_password(form.password.data):
			login_user(user, form.remember_me.data)
			current_user.ping()
			return redirect(url_for('index')) 
	return render_template('login.html', form = form)

@app.route('/logout')
@login_required
def logout():
	logout_user()
	flash('You have been logged out.')
	return redirect(url_for('index'))


@app.route('/register', methods = ['GET', 'POST'])
def register():
	form = RegisterForm()
	if form.validate_on_submit():
		email_test = User.query.filter_by(email = form.email.data).first()
		username_test = User.query.filter_by(username = form.username.data).first()
		if email_test or username_test:
			return 'Email or Username already registered'
		user = User(email = form.email.data,
			username = form.username.data,
			password = form.password.data)
		db.session.add(user)
		db.session.commit()
		return redirect(url_for('login'))
	return render_template('register.html', form = form)

	
@app.route('/edit/<int:id>', methods = ['GET', 'POST'])
@login_required
def edit(id):
	post = Post.query.get_or_404(id)
	if current_user != post.author and \
	not current_user.can(Permission.ADMINISTER):
		abort(403)
	form = PostForm()
	if form.validate_on_submit():
		post.body = form.body.data
		db.session.add(post)
		flash('The post has been updated.')
		return redirect(url_for('edit', id = post.id))
	form.body.data = post.body
	return render_template('edit_post.html', form = form)

@app.route('/post/<int:id>', methods = ['GET', 'POST'])
def post(id):
	post = Post.query.get_or_404(id)
	form = CommentForm()
	if form.validate_on_submit():
		comment = Comment(body = form.body.data,
		author = current_user._get_current_object(), post_id = id)
		db.session.add(comment)
		# db.session.commit()
		flash('Your comment had been published.')
		return redirect(url_for('post', id = id, page = -1))
	page = request.args.get('page', 1, type = int)
	if page == -1:
		page = (post.comments.count() - 1) // config.MING_COMMENTS_PER_PAGE + 1
	pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
		page, per_page = config.MING_COMMENTS_PER_PAGE, error_out = False)
	comments = pagination.items
	return render_template('post.html', posts = [post], form = form,
		comments = comments, pagination = pagination, Permission = Permission)


@app.route('/test')
@login_required
def test():
	return 'login required test'

@app.route('/changepassword', methods = ['GET', 'POST'])
@login_required
def changepassword():
	form = ChangePasswordForm()
	if form.validate_on_submit():
		if current_user.verify_password(form.old_password.data):
			current_user.password = form.password.data
			db.session.add(current_user)
			db.session.commit()
			return 'Change password successfully'
		else:
			flash('Invalid Password.')
	return render_template('changepassword.html', form = form)

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

@app.route('/user/<username>')
def user(username):
	user = User.query.filter_by(username = username).first()
	if user is None:
		abort(404)
	posts = user.posts.order_by(Post.timestamp.desc()).all()
	return render_template('user.html', user = user, posts = posts)

@app.route('/edit-profile', methods = ['GET', 'POST'])
@login_required
def edit_profile():
	form = EditProfileForm()
	if form.validate_on_submit():
		current_user.name = form.name.data
		current_user.location = form.location.data
		current_user.about_me = form.about_me.data
		db.session.add(current_user)
		flash('You profile has been updated.')
		return redirect(url_for('user', username = current_user.username))
	form.name.data = current_user.name 
	form.location.data = current_user.location
	form.about_me.data = current_user.about_me
	return render_template('edit_profile.html', form = form)


@app.route('/edit-profile/<int:id>', methods = ['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
	user = User.query.get_or_404(id)
	form = EditProfileAdminForm(user)
	if form.validate_on_submit():
		user.email = form.email.data
		user.username = form.username.data
		user.location = form.location.data
		user.confirmed = form.confirmed.data
		user.role = Role.query.get(form.role.data)
		user.name = form.name.data
		user.about_me = form.about_me.data
		db.session.add(user)
		flash('The profile has been updated.')
		return redirect(url_for('user', username = user.username))
	form.email.data = user.email
	form.username.data = user.username
	form.confirmed.data = user.confirmed
	form.role.data = user.role_id
	form.name.data = user.name
	form.location.data = user.location
	form.about_me.data = user.about_me
	return render_template('edit_profile.html', form = form, user = user)