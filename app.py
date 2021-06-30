from flask import Flask, render_template, request, redirect, url_for, session, flash,json
from flask_mysqldb import MySQL
from datetime import datetime
import MySQLdb.cursors
import re
import os
import uuid
import random

app = Flask(__name__)

pageLimit =5

app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = os.urandom(24)
app.config['MYSQL_HOST'] = 'host_link'
app.config['MYSQL_USER'] = 'username@servername'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'user'
app.config['UPLOAD_FOLDER'] = 'static/Uploads'

mysql = MySQL(app)
user_id = os.urandom(24)
post_user_id = user_id
@app.route('/')
def index():
	return render_template('index.html')

@app.route('/login', methods =['GET', 'POST'])
def login():
	msg = ''
	if request.method == 'POST' and 'username' in request.form and 'phonenumber' in request.form:
		username = request.form['username']
		number = request.form['phonenumber']
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM user WHERE name = %s AND phonenumber = %s', (username, number,))
		account = cursor.fetchone()
		if account: #wher user_id = token, 
			session['status'] = 1
			session['name'] = account['name']
			session['number'] = account['phonenumber']
			msg = 'Logged in successfully !'
			return render_template('userHome.html', msg = msg)
		else:
			msg = 'Incorrect Name / PhoneNumber!'
			return render_template('login.html', msg = msg)
	else:
		return render_template('login.html')

@app.route('/logout')
def logout():
	session.pop('loggedin', None)
	session.pop('username', None)
	return redirect(url_for('login'))

@app.route('/showDashboard')
def showDashboard():
    return render_template('dashboard.html')

@app.route('/register', methods =['GET', 'POST'])
def register():
	msg = ''
	if request.method == 'POST' and 'username' in request.form and 'phonenumber' in request.form and 'email' in request.form :
		username = request.form['username']
		number = request.form['phonenumber']
		email = request.form['email']
		now = datetime.now()
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM user WHERE name = % s', (username, ))
		account = cursor.fetchone()
		if account:
			msg = 'Account already exists !'
		elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
			msg = 'Invalid email address !'
		elif not re.match(r'[A-Za-z0-9]+', username):
			msg = 'Username must contain only characters and numbers !'
		elif not username or not number or not email:
			msg = 'Please fill out the form !'
		else:
			cursor.execute('INSERT INTO user(name,phonenumber,email,created_at) VALUES (%s, %s, %s, %s)', (username, number, email,now ))
			mysql.connection.commit()
			msg = 'You have successfully registered !'
	elif request.method == 'POST':
		msg = 'Please fill out the form !'
	return render_template('register.html', msg = msg)
	
@app.route('/userHome', methods=['GET', 'POST'])
def userHome():
        return render_template('userHome.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
	if request.method=='POST':
		file = request.files['file']
		extension =os.path.splitext(file.filename)[1]
		f_name = str(uuid.uuid4()) + extension
		file.save(os.path.join(app.config['UPLOAD_FOLDER'],f_name))
		return json.dumps({'filename':f_name})

@app.route('/addPage',methods=['GET','POST'])
def addPage():
	if request.method == 'POST' and 'inputTitle' in request.form and 'inputDescription' in request.form:
		title = request.form['inputTitle']
		description = request.form['inputDescription']
		post_id = random.randrange(10)
		now = datetime.now()
		_user ='1'
		if request.form.get('filePath') is None:
			filepath = ''
		else:
			filepath = request.form.get('filePath')
		if request.form.get('done') is None:
			_done = 0
		else:
			_done = 1
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		#cursor.execute('INSERT INTO tbl_post(post_id,post_title, post_description,post_uploaded_path, post_user_id, post_date) VALUES (%s, %s, %s, %s, %s, %s)', (post_id,title, description,filepath,_user, now ))
		cursor.callproc('sp_addWish',(title,description,_user,filepath,_done))
		data = cursor.fetchall()
		if len(data) == 0:
			mysql.connection.commit()
			return redirect('/userHome')
        
	elif request.method=='POST':
		return render_template('error.html',error = 'An error occurred!')
		
	else:
		return render_template('addWish.html',error = 'Unauthorized Access')

@app.route('/showAddPage',methods=['GET','POST'])
def showAddPage():
	return render_template('addWish.html')

@app.route('/getPage',methods=['GET'])
def getPage():
		#user = session.get('user')
		_user = '1'
		limit = pageLimit
		offset = request.form['offset']
		total_records = 0
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.callproc('sp_GetWishByUser',_user,limit,offset,total_records)
		wishes = cursor.fetchall()
		#cursor = cursor.execute("SELECT * FROM tbl_wish WHERE wish_user_id =%s", (_user))
		cursor.execute('Select @sp_GetWishByUser_3')
		outParam = cursor.fetchall()
		response = []
		wishes_dict = []
		for wish in wishes:
			wish_dict = {
				'Id': wish[0],
				'Title': wish[1],
				'Description': wish[2],
				'Date': wish[4]}
			wishes_dict.append(wish_dict)
			response.append(wishes_dict)
			response.append({'total':outParam[0][0]})
		return json.dumps(response)
		#return render_template('error.html',error = 'Unauthorized Access')

@app.route('/getPageById',methods=['GET','POST'])
def getPageById():
    try:
        if session.get('user'):
            
            _id = request.form['id']
            _user = '1'
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM tbl_wish WHERE wish_id =%s AND wish_user_id =%s',(_id,_user))
            result = cursor.fetchall()
            wish = []
            wish.append({'Id':result[0][0],'Title':result[0][1],'Description':result[0][2],'FilePath':result[0][3],'Done':result[0][5]})
            return json.dumps(wish)
        else:
            return render_template('error.html', error = 'Unauthorized Access')
    except Exception as e:
        return render_template('error.html',error = str(e))

@app.route('/getAllWishes')
def getAllWishes():
    try:
        if session.get('user'):
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('Select * FROM tbl_wish')
            result = cursor.fetchall()
            wishes_dict = []
            for wish in result:
                wish_dict = {
                        'Id': wish[0],
                        'Title': wish[1],
                        'Description': wish[2],
                        'FilePath': wish[3]}
                wishes_dict.append(wish_dict)		
            return json.dumps(wishes_dict)
        else:
            return render_template('error.html', error = 'Unauthorized Access')
    except Exception as e:
        return render_template('error.html',error = str(e))

if __name__ == '__main__':
	app.run(debug=True)
