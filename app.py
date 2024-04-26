from flask import Flask, render_template, request, redirect, url_for,jsonify
import requests
from pymongo import MongoClient
import bcrypt
from bson.objectid import ObjectId 
import os
from dotenv import load_dotenv
from flask_cors import CORS
import secrets
import string
import base64


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
    users = [{"username": user["username"], "email": user["email"],"_id":user['_id'],"password":user["password"],"image":user['image'].decode('utf-8')} for user in users]
    return render_template('home.html', users=users)



## crud 

## create -- create a user register function 
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        file = request.files['image']
        # Read the contents of the file
        file_contents = file.read()
        # Encode the file contents to base64
        encoded_contents = base64.b64encode(file_contents)
        # Extract other registration data from the request
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12))

        # Create a user object with image and other data
        user_data = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "image": encoded_contents
        }
        # Insert the user object into the users collection
        users_collection.insert_one(user_data)
        return "Registration successful! User added to the database."
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
        new_image = request.files['image'] if 'image' in request.files else None

        # Prepare the updated data
        update_data = {}
        if username:
            update_data['username'] = username
        if email:
            update_data['email'] = email
        if password:
            update_data['password'] = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12))
        if new_image:
            # Read the contents of the file
            file_contents = new_image.read()
            # Encode the file contents to base64
            encoded_contents = base64.b64encode(file_contents)
            update_data['image'] = encoded_contents

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
    

## using api -- weather example using weather.html + js to handle responses from server 

api_key = os.getenv('API_KEY')
api_base_url = os.getenv('API_BASE_URL')

@app.route('/weather', methods=['GET', 'POST'])
def weather():
    if request.method == 'GET':
        return render_template('weather.html')
    
    if request.method == 'POST':
        city = request.form.get('city')
        location_code = get_location_code(city)
        if location_code:
            current_weather = get_current_weather(location_code)
            return jsonify(current_weather)
        else:
            return jsonify({'error': 'City not found'})
    
def get_location_code(city):
    url = f'{api_base_url}/locations/v1/cities/autocomplete/?apikey={api_key}&q={city}&language=en-us'
    response = requests.get(url)
    data = response.json()
    if data:
        return data[0]['Key']
    else:
        return None    
    
def get_current_weather(location_code):
    url = f'{api_base_url}/currentconditions/v1/{location_code}?apikey={api_key}&language=en-us&details=true'
    print(url)
    response = requests.get(url)
    data = response.json()
    if data:
        return {
            'date': data[0]['LocalObservationDateTime'],
            'temperature': data[0]['Temperature']['Metric']['Value'],
            'weather_text': data[0]['WeatherText'],
            'weather_icon': data[0]['WeatherIcon']
        }
    else:
        return None




## bitly project page - 


@app.route('/shorten', methods=['GET','POST'])
def shorten_url():
    if request.method == 'GET':
        return render_template('shorten_url.html')
    if request.method == 'POST':
        long_url = request.form['long_url']
        short_identifier = generate_unique_identifier()
        url_mapping = {
            'short_url': short_identifier,
            'long_url': long_url
        }
        db.url_mappings.insert_one(url_mapping)
        return f"Shortened URL: <a href='/u/{short_identifier}'>{request.host+'/' + short_identifier}</a>"

@app.route('/u/<short_identifier>')
def redirect_to_long_url(short_identifier):
    url_mapping = db.url_mappings.find_one({'short_url': short_identifier})
    
    if url_mapping:
        return redirect(url_mapping['long_url'])
    else:
        return "Short URL not found"

def generate_unique_identifier(length=8):
    """Generate a random alphanumeric string."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
