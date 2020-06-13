from flask import Flask, request, render_template, url_for, request, json, g, session, redirect, send_from_directory
import mysql.connector
import yaml
import io
import os
import re


UPLOAD_FOLDER = '/home/pd/Documents/dipl/Service_AD_one/profile/'
ALLOWED_EXTENSIONS = set(['yaml'])

app = Flask(__name__)
app.secret_key = 'secret_key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def user_statys():
	cursor = g.conn.cursor()
	cursor.execute("select text_status, user_status, status_privat from status ORDER BY status_id DESC LIMIT 10")
	data_status = cursor.fetchall()
	cursor.close()
	return data_status


@app.before_request
def connect_db():
    g.conn = mysql.connector.connect(
        host='0.0.0.0',
        database='BucketList',
        user='user_one',
        password='12345678'
    )


@app.route('/reg',methods=['GET','POST'])
def register():
	if 'username' in session:
		return redirect(url_for('index'))

	if request.method == 'GET':
		return render_template('register.html')

	if request.method == 'POST':
		content = request.form
		name = request.form.get("name", "")
		email = request.form.get("email", "")
		password = request.form.get("password", "")

		if name and email and password:
			cursor = g.conn.cursor()
			cursor.execute("select user_name from tbl_user where user_name=%s", (name, ))

			if cursor.fetchall():
				cursor.close()
				return json.dumps({'html':'<span>User allredi exist</span>'})

			else:
				cursor.execute("insert into tbl_user (user_name, user_username, user_password) values (%s, %s, %s)",(name, email, password))
				g.conn.commit()
				cursor.close()
				return redirect(url_for('login'))
		else:
			return json.dumps({'html':'<span>Enter the required fields</span>'})


@app.route('/log', methods=['GET', 'POST'])
def login():
	if 'username' in session:
		return redirect(url_for('index'))

	if request.method == 'GET':
		return render_template('login.html')

	if request.method == 'POST':
		content = request.form
		name = request.form.get("name", "")
		password = request.form.get("password", "")

		if name and password:
			cursor = g.conn.cursor()
			cursor.execute("select user_name, user_password from tbl_user where user_name=%s and user_password=%s", (name,password,))

			if cursor.fetchall():
				session['username'] = name
				cursor.close()
				return redirect(url_for('profile', username = name))
			else:
				return json.dumps({'html':'<span>User not found</span>'})

		else:
			return json.dumps({'html':'<span>Enter the required fields</span>'})


@app.route('/profile/<username>', methods=['GET','POST'])
def profile(username):
	if request.method == 'GET':
		name = re.sub('[^a-zA-Z0-9]', '', username)
		cursor = g.conn.cursor()
		cursor.execute("select user_username from tbl_user where user_name=%s", (name, ))
		data_user = cursor.fetchone()
		cursor.execute("select city,telefon_number,year_of_birth,secret from user_info where name_user=%s", (name, ))
		data_info = cursor.fetchall()
		if data_user != None:
			cursor.close()
			return render_template('profile.html', data = data_user, info = data_info, username = username)
		else:
			return json.dumps({'html':'<span>Takogo usera sdes net</span>'})

	if request.method == 'POST':
		if 'btn_file' in request.form:
			file = request.files['yaml']
			filename = session['username'] + '.yaml'
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			with open('profile/'+filename) as stream:
				data_loaded = yaml.load(stream)
			name = session['username']	
			city = data_loaded['City']
			telefon_number = data_loaded['Tel']
			year_of_birth = data_loaded['Year']
			secret = data_loaded['Secret'] 

			if city and telefon_number and year_of_birth:
				cursor = g.conn.cursor()
				cursor.execute("select name_user from user_info where name_user=%s", (username, ))
				if cursor.fetchall():
					cursor.execute("update user_info set city=%s, telefon_number=%s, year_of_birth=%s, secret=%s where name_user=%s",(city, telefon_number, year_of_birth, secret, name))
				else:
					cursor.execute("insert into user_info (name_user, city, telefon_number, year_of_birth, secret) values (%s, %s, %s, %s, %s)",(name, city, telefon_number, year_of_birth, secret))
				g.conn.commit()
				cursor.close()
				return redirect(url_for('profile', username = name))
			else:
				return json.dumps({'html':'<span>file ne och</span>'})

		else:
			content = request.form
			name = session['username']
			city = request.form.get("city", "")
			telefon_number = request.form.get("telefon_number", "")
			year_of_birth = request.form.get("year_of_birth", "")
			secret = request.form.get("secret", "")

			if city and telefon_number and year_of_birth:
				cursor = g.conn.cursor()
				cursor.execute("select name_user from user_info where name_user=%s", (name, ))
				if cursor.fetchall():
					cursor.execute("update user_info set city=%s, telefon_number=%s, year_of_birth=%s, secret=%s where name_user=%s",(city, telefon_number, year_of_birth, secret, name))
				else:
					cursor.execute("insert into user_info (name_user, city, telefon_number, year_of_birth, secret) values (%s, %s, %s, %s, %s)",(name, city, telefon_number, year_of_birth, secret))
				g.conn.commit()
				cursor.close()
				return redirect(url_for('profile', username = name))
			else:
				return json.dumps({'html':'<span>Zapolni oll polia</span>'})
		


@app.route('/user_list', methods=['GET'])
def user_list():
	if request.method == 'GET' and 'admin' in session['username']:
		cursor = g.conn.cursor()
		cursor.execute("select user_name from tbl_user")
		data_user = cursor.fetchall()
		if data_user == None:
			return json.dumps({'html':'<span>Tyt poka nikogo net</span>'})
		else:
			return render_template('list.html', data = data_user)
	else:
		return json.dumps({'html':'<span>Y tebia sdesi net vlasti</span>'})

@app.route("/", methods=['GET', 'POST'])
def index():

	if request.method == 'GET':
		return render_template('index.html', data = user_statys())

	if request.method == 'POST':
		content = request.form
		username = session['username']
		text = request.form.get("text_status", "")
		privat = request.form.get("privat", "")

		if privat == '':
			privat = 0
		else:
			privat = 1
		
		if text:
			cursor = g.conn.cursor()
			cursor.execute("insert into status (text_status, user_status, status_privat) values (%s, %s, %s)",(text, username, privat))
			g.conn.commit()
			cursor.execute("select text_status from status")
			data_status = cursor.fetchall()
			cursor.close()
			return render_template('index.html', data = user_statys())
		else:
			return json.dumps({'html':'<span>Vash status is veri pyst</span>'})

@app.route('/logout')
def logout():
    session.pop("username", None)
    return redirect(url_for('login'))

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=5000)
