# -*- coding: utf-8 -*-
from flask import Flask, request, render_template, url_for, request, json, g, session, redirect, jsonify, send_file
from werkzeug.utils import secure_filename
import json
import mysql.connector
import jwt
import os

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.secret_key = '(Q_Q)'

@app.before_request
def connect_db():
    g.conn = mysql.connector.connect(
        host='0.0.0.0',
        database='Dyranki',
        user='user_one',
        password='12345678'
    )


@app.route('/register',methods=['GET','POST'])
def register():
	if 'username' in session:
		return redirect(url_for('index'))

	if request.method == 'GET':
		return render_template('register.html')

	if request.method == 'POST':
		content = request.form
		username = request.form.get("username", "")
		password = request.form.get("password", "")

		if username and password:
			cursor = g.conn.cursor()
			cursor.execute("select login from users where login=%s", (username, ))

			if cursor.fetchall():
				cursor.close()
				return json.dumps({'html':'<span>User allredi exist</span>'})

			else:
				cursor.execute("insert into users (login, password) values (%s, %s)",(username, password,))
				g.conn.commit()
				cursor.close()
				return redirect(url_for('login'))
		else:
			return json.dumps({'html':'<span>Enter the required fields</span>'})


@app.route('/login', methods=['GET', 'POST'])
def login():
	if 'username' in session:
		return redirect(url_for('index'))

	if request.method == 'GET':
		return render_template('login.html')

	if request.method == 'POST':
		content = request.form
		username = request.form.get("username", "")
		password = request.form.get("password", "")

		if username and password:
			cursor = g.conn.cursor()
			cursor.execute("select login, password from users where login='%s' and password='%s'" % (username, password))
			if cursor.fetchall():
				token = jwt.encode({'user': username}, 'secret', algorithm='HS256')
				res = redirect(url_for('index'))
				res.set_cookie('jwt', token)
				cursor.close()
				return res
			else:
				cursor.close()
				return json.dumps({'html':'<span>User not found</span>'})

		else:
			return json.dumps({'html':'<span>Enter the required fields</span>'})


@app.route("/admin", methods=['GET'])
def admin():
	token = request.cookies.get('jwt')
	decode = jwt.decode(token, 'secret', algorithms=['HS256'])
	username = decode['user']
	if username == 'admin':
		return render_template('admin.html', admin=True)
	else:
		return redirect(url_for('index'))


@app.route("/profile", methods=['GET', 'POST'])
def profile():
	token = request.cookies.get('jwt')
	if not token:
		return redirect(url_for('login'))
	decode = jwt.decode(token, 'secret', algorithms=['HS256'])
	username = decode['user']

	if request.method == 'GET':

		try:
			text = open('bio/'+username+'/bio.txt', 'r')
			text = text.read()
		except:
			text = ''
		try:
			file = os.listdir('static/'+username+'/')
		except:
			file = ''
			
		return render_template('profile.html', username = username, pictures=file, data=text) 

	if request.method == 'POST':

		if request.form['action'] == 'file_upload':
			file = request.files['file']
			if file and (file.content_type.rsplit('/', 1)[1] in ALLOWED_EXTENSIONS).__bool__():
				filename = secure_filename(file.filename)
				os.makedirs('static/'+username)
				file.save('static/'+ username + '/' + filename)
				return redirect(url_for('profile'))

		if request.form['action'] == 'btn_text':
			text = request.form.get("text", "")
			if not os.path.isdir("bio/"+username):
				os.makedirs('bio/'+username)
				f = open('bio/'+ username + '/' + 'bio.txt', 'w')
				f.write(text + '\n')
				f.close()
				return redirect(url_for('profile'))
			else:
				f = open('bio/'+ username + '/' + 'bio.txt', 'a')
				f.write(text + '\n')
				f.close()
				return redirect(url_for('profile'))


@app.route("/profile/download", methods=['GET'])
def download():
	token = request.cookies.get('jwt')
	if not token:
		return redirect(url_for('login'))
	decode = jwt.decode(token, 'secret', algorithms=['HS256'])
	username = decode['user']

	pic_name = request.args.get('name', '')
	if pic_name:
		part = 'static/'+username+'/'+ pic_name
		return send_file(part, as_attachment=True)
	else:
		return json.dumps({'html':'<span>net get parametra</span>'})


@app.route("/add_post", methods=['GET','POST'])
def addpost():
	token = request.cookies.get('jwt')
	if not token:
		return redirect(url_for('login'))
	decode = jwt.decode(token, 'secret', algorithms=['HS256'])
	username = decode['user']

	if request.method == 'GET':
		return render_template('addpost.html')

	if request.method == 'POST':
		content = request.form
		title = request.form.get("name_title", "")
		info = request.form.get("info", "")
		time = request.form.get("time", "")
		file = request.files['pictures']

		if not title or not info or not time or not file:
			return json.dumps({'html':'<span>zapolni vse</span>'})
		else:

			if file and (file.content_type.rsplit('/', 1)[1] in ALLOWED_EXTENSIONS).__bool__():
				filename = secure_filename(file.filename)
				file.save('static/posts/' + filename)
			else:
				return json.dumps({'html':'<span>che ne foto</span>'})

			cursor = g.conn.cursor()
			cursor.execute("insert into posts (username, title, time, info, pic_name) values (%s, %s, %s, %s, %s)",(username, title, time, info, filename))
			g.conn.commit()
			cursor.close()
		
		return redirect(url_for('index'))


@app.route("/post/<int:n_post>", methods=['GET'])
def post(n_post):
	token = request.cookies.get('jwt')
	if not token:
		return redirect(url_for('login'))
	decode = jwt.decode(token, 'secret', algorithms=['HS256'])
	username = decode['user']

	if request.method == 'GET':
		cursor = g.conn.cursor()
		cursor.execute("select * from posts where id=%s",(n_post,))
		post = cursor.fetchone()
		cursor.close()
		return render_template('post.html', post = post)


@app.route("/", methods=['GET'])
def index():
	token = request.cookies.get('jwt')
	if not token:
		return redirect(url_for('login'))
	decode = jwt.decode(token, 'secret', algorithms=['HS256'])
	username = decode['user']

	if request.method == 'GET':

		cursor = g.conn.cursor()
		cursor.execute("select * from posts ")
		post = cursor.fetchall()
		cursor.close()
		return render_template('index.html' ,data = username, post=post)

			
@app.route('/logout')
def logout():
    res = redirect(url_for('login'))
    res.set_cookie('jwt', 'bar', max_age=0)
    return res

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=7777)
