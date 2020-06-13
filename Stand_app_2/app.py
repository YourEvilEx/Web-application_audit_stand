from flask import Flask, request, render_template, url_for, request, json, g, session, redirect
import mysql.connector


app = Flask(__name__)
app.secret_key = 'secret_key'

@app.before_request
def connect_db():
    g.conn = mysql.connector.connect(
        host='0.0.0.0',
        database='BadEnd',
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
		balance = 1000

		if username and password:
			cursor = g.conn.cursor()
			cursor.execute("select login from users where login=%s", (username, ))

			if cursor.fetchall():
				cursor.close()
				return json.dumps({'html':'<span>User allredi exist</span>'})

			else:
				cursor.execute("insert into users (login, password, balance) values (%s, %s, %s)",(username, password, balance,))
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
			cursor.execute("select login, password from users where login=%s and password=%s", (username, password,))

			if cursor.fetchall():
				session['username'] = username
				cursor.close()
				return redirect(url_for('index'))
			else:
				cursor.close()
				return json.dumps({'html':'<span>User not found</span>'})

		else:
			return json.dumps({'html':'<span>Enter the required fields</span>'})


@app.route('/post/<post_id>', methods=['GET','POST'])
def post(post_id):

	if request.method == 'GET':
		cursor = g.conn.cursor()
		cursor.execute("select author, price from posts where id=%s", (post_id,))
		post = cursor.fetchone()
		cursor.close()
		if post:
			return render_template('post.html', post = post)
		else:
			return json.dumps({'html':'<span>Post ne syshestvyet</span>'})

	if request.method == 'POST':

		username = session['username']
		cursor = g.conn.cursor()
		cursor.execute("select price from posts where id=%s", (post_id,))
		price = cursor.fetchone()
		price = int(price[0])
		cursor.execute("select balance from users where login=%s", (username,))
		balance = cursor.fetchone()
		balance = int(balance[0])

		if balance > price:
			cursor.execute("select text from posts where id=%s", (post_id,))
			text = cursor.fetchone()
			cursor.execute("""update users set balance = balance - %s where login = %s""",(price, username)) 
			g.conn.commit()
			cursor.close()
			return render_template('post.html', text = text)
		else:
			cursor.close()
			return json.dumps({'html':'<span>Иди работать бедняг</span>'})


@app.route('/users', methods=['GET'])
def user_list():
	if 'username' in session:
		cursor = g.conn.cursor()
		cursor.execute("select login from users")
		user_list = cursor.fetchall()
		cursor.close()
		return render_template('list.html', data = user_list)
	else:
		return json.dumps({'html':'<span>User not in session</span>'})


@app.route('/profile', methods=['GET'])
def profile():
	if 'username' not in session:
		return redirect(url_for('login'))

	username = session['username']
	cursor = g.conn.cursor()
	cursor.execute("select balance from users where login=%s", (username,))
	balance = cursor.fetchone()
	cursor.execute("select text, price from posts where author=%s", (username,))
	posts = cursor.fetchall()
	cursor.close()
	return render_template('profile.html', username = username, balance = balance, posts = posts)


@app.route("/", methods=['GET', 'POST'])
def index():

	if request.method == 'GET':

		cursor = g.conn.cursor()
		cursor.execute("select id,author,price from posts order by id desc limit 10")
		post_list = cursor.fetchall()
		cursor.close()
		return render_template('index.html', data  = post_list)

	if request.method == 'POST':

		if request.form['action'] == 'btn_edit_end':
			username = session['username']
			text = request.form.get("text", "")
			price = request.form.get("price", "")

			if text and price:
				cursor = g.conn.cursor()
				cursor.execute("insert into posts (author, text, price) values (%s, %s, %s)",(username, text, price,))
				g.conn.commit()
				cursor.close()

				return redirect(url_for('index'))

			else:

				return json.dumps({'html':'<span>Not data</span>'})

		if request.form['action'] == 'search':
			author = request.form.get("text", "")
			print(author)
			cursor = g.conn.cursor()
			cursor.execute("select id,author,price from posts where author='%s'" % (author))
			data = cursor.fetchall()
			print(data)
			return render_template('index.html', data  = data)

		if 'posts' in request.form['action']:
			idd = request.form['action'].replace('posts_','')
			return redirect(url_for('post', post_id = idd))



@app.route('/logout')
def logout():
    session.pop("username", None)
    return redirect(url_for('login'))

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=8080)
