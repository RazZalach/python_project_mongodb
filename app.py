from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
import bcrypt
from bson.objectid import ObjectId 
import os
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()
# פרטי התחברות למסד הנתונים
connection_string = os.getenv('MONGODB_CONNECTION_STRING')
client = MongoClient(connection_string)
db = client['python_project']
users_collection = db['users']

app = Flask(__name__, static_folder='static')
CORS(app)


@app.route('/')
def home():
    users = list(users_collection.find({}))
    users = [{"username": user["username"], "email": user["email"],"_id":user['_id'],"password":user["password"]} for user in users]
    return render_template('home.html', users=users)



## crud 

## create -- create a user register function 
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # בדיקה אם האימייל כבר קיים במסד הנתונים
        if users_collection.find_one({"email": email}):
            return "This email is already registered. Try another email.</br> <a href='/register'>Try Again</a>"

        # הצפנת הסיסמה
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12))
        
        # שמירת המשתמש במסד הנתונים
        user_data = {
            "username": username,
            "email": email,
            "password": hashed_password  # שומרים את הסיסמה המוצפנת
        }
        users_collection.insert_one(user_data)

        return "Registration successful! </br> <a href='/'>Home</a>"
    
    return render_template('register.html')

## read a user data 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = users_collection.find_one({"email": email})
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            return "Login successful! </br> <a href='/'>Home</a>"
        else:
            return "Invalid email or password. </br> <a href='/login'>Try Again</a>"

    return render_template('login.html')

## update a user
@app.route('/update_user/<user_id>', methods=['GET', 'POST'])
def update_user(user_id):
    if request.method == 'POST':
        # Fetch the form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Prepare the updated data
        update_data = {}
        if username:
            update_data['username'] = username
        if email:
            update_data['email'] = email
        if password:
            update_data['password'] = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12))

        # Update the user in the database
        users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': update_data})

        return redirect(url_for('home'))
    else:
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        if not user:
            return "User not found"

        return render_template('update_user.html', user=user)


## delete a user 
@app.route('/delete_user/<user_id>', methods=['POST'])
def delete_user(user_id):
    try:
        users_collection.delete_one({"_id": ObjectId(user_id)})
        return redirect(url_for('home'))
    except Exception as e:
        return str(e)  

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
