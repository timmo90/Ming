# -*- coding: utf-8 -*-

from ming import db, login_manager
from flask_login import UserMixin, AnonymousUserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import config
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


class Permission:
	FOLLOW = 0X01
	COMMENT = 0X02
	WRITE_ARTICLES = 0X04
	MODERARE_COMMMETS = 0X08
	ADMINISTER = 0X80

class Role(db.Model):
	__tablename__ = 'roles'
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(64), unique = True)
	default = db.Column(db.Boolean, default = False, index = True)
	permissions = db.Column(db.Integer)
	users = db.relationship('User', backref = 'role', lazy = 'dynamic')

	@staticmethod
	def inser_roles():   # or inser into roles manually
		roles = {
		'User': (Permission.FOLLOW |
			Permission.COMMENT |
			Permission.WRITE_ARTICLES, True),
		'Moderator': (Permission.FOLLOW |
			Permission.COMMENT |
			Permission.WRITE_ARTICLES |
			Permission.MODERARE_COMMMETS, False),
		'Administrator': (0xff, False)
		}
		for r in roles:
			role = Role.query.filter_by(name = r).first()
			if role is None:
				role = Role(name = r)
			role.permissions = roles[r][0]
			role.default = roles[r][1]
			db.session.add(role)
		db.session.commit()


class Follow(db.Model):
	__tablename__ = 'follows'
	follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key = True)
	followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key = True)
	timestamp = db.Column(db.DateTime, default = datetime.utcnow)
		

class User(UserMixin, db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key = True)
	email = db.Column(db.String(64), unique = True, index = True)
	username = db.Column(db.String(64), unique = True, index = True)
	role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
	password_hash = db.Column(db.String(128))
	confirmed = db.Column(db.Boolean, default = False)
	name = db.Column(db.String(64))
	location = db.Column(db.String(64))
	about_me = db.Column(db.Text())
	member_since = db.Column(db.DateTime(), default = datetime.utcnow)
	last_seen = db.Column(db.DateTime(), default = datetime.utcnow)
	avatar_hash = db.Column(db.String(32))
	posts = db.relationship('Post', backref = 'author', lazy = 'dynamic')
	# followed = db.relationship('Follow', foreign_keys = [Follow.follower_id],
	# 	backref = db.backref('follower', lazy = 'joined'), lazy = 'dynamic',
	# 	cascade = 'all, delete-orphan')
	# followers = db.relationship('Follow', foreign_keys = [Follow.followed_id],
	# 	backref = db.backref('followed', lazy = 'joined'),
	# 	lazy = 'dynamic', cascade = 'all, delete-orphan')
	comments = db.relationship('Comment', backref = 'author', lazy = 'dynamic')

	def __init__(self, **kwargs):
		super(User, self).__init__(**kwargs) # how does it work?
		self.email = kwargs['email']
		self.username = kwargs['username']
		self.password_hash = generate_password_hash(kwargs['password'])

		if self.email == 'moyitian90@163.com':
			self.role = Role.query.filter_by(permissions = 0xff).first()
		if self.role is None:
			self.role = Role.query.filter_by(default = True).first()
		# if kwargs.get():
		# 	pass
		

	@property
	def password(self):
		raise AttributeError('Password is not a readable attribute')

	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)

	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)

	def ping(self):
		self.last_seen = datetime.utcnow()
		db.session.add(self)

	def generate_confirmation_token(self, expiration = 3600):
		s = Serializer(config.SECRET_KEY, expiration)
		return s.dumps({'confirm': self.id})

	def confirm(self, token):
		s = Serializer(config.SECRET_KEY)
		try:
			data = s.loads(token)
		except:
			return False
		if data.get('confirm') != self.id:
			return False
		self.confirmed = True
		ab.session.add(self)
		return True

	def can(self, permissions):
		return self.role is not None and (self.role.permissions & permissions)\
		 == permissions
		
	def is_administrator(self):
		return self.can(Permission.ADMINISTER)

class AnonymousUser(AnonymousUserMixin):
	def can(self, permissions):
		return False

	def is_administrator(self):
		return False

login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(userid):
    return User.query.get(int(userid))


class Post(db.Model):
	__tablename__ = 'posts'
	id = db.Column(db.Integer, primary_key = True)
	body = db.Column(db.Text)
	body_html = db.Column(db.Text)
	timestamp = db.Column(db.DateTime, index = True, default = datetime.utcnow)
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	comments = db.relationship('Comment', backref = 'post', lazy = 'dynamic')

	def __init__(self, body, author):
		self.body = body
		self.author = author

	@staticmethod
	def generate_fake(count = 50):
		from random import seed, randint
		import forgery_py

		seed()
		user_count = User.query.count()
		for i in range(count):
			u = User.query.offset(randint(0, user_count - 1)).first()
			body = forgery_py.lorem_ipsum.sentences(randint(1, 5))
			# timestamp = forgery_py.date.date(True)
			p = Post(body, u)
			db.session.add(p)
			db.session.commit()

class Comment(db.Model):
	__tablename__ = 'comments'
	id = db.Column(db.Integer, primary_key = True)
	body = db.Column(db.Text)
	body_html = db.Column(db.Text)
	timestamp = db.Column(db.DateTime, default = datetime.utcnow)
	disabled = db.Column(db.Boolean)
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

	def __init__(self, body, author, post_id):
		self.body = body
		self.author = author
		self.post_id = post_id  # self.post_id = post_id	