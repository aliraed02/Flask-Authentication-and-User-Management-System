import sqlite3
from flask import Flask, request, jsonify, g
import secrets
import os
from datetime import datetime
import re
import jwt
from datetime import datetime, timedelta, date




app = Flask(__name__)
app.config['SECRET_KEY'] = "SECRET_KEY"




def connect():
    
    db = getattr(g, 'database5', None)
    if db is None:
        db = g._database = sqlite3.connect('database5.db')
    return db






def table_exists():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='login'")
    result = cursor.fetchone()
    return result is not None






@app.route('/create_table')
def create_table():
    conn = connect()
    cursor = conn.cursor()
    # SQL query to create the table
    create_table_query = '''
        CREATE TABLE login (
            email TEXT PRIMARY KEY,
            password TEXT,
            is_admin INTEGER CHECK (is_admin IN (0, 1)),
            img text
            
        )
    '''
    cursor.execute(create_table_query)
    conn.commit()
    conn.close()
    return 'Table created successfully!'








@app.route('/')
def home():
    if table_exists():
        return 'Table exists!'
    else:
        create_table()
        return 'Table does not exist!'














JWT_SECRET = 'SECRET_KEY'
JWT_EXPIRATION_HOURS = 24


def generate_token(user_id):

    payload = {
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow(),
        'sub': user_id
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    
    if isinstance(token, bytes):
        return token.decode('utf-8')
    
    return token








def verify_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return 'Token expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'








@app.route('/add', methods=['POST'])
def handle_post():
    conn = connect()
    cursor = conn.cursor()

    
    
    param1 = request.form.get('Email')
    param2 = request.form.get('password')
    param3 = request.form.get('IsAdmin')
    file = request.files['Picture']
    #name = file.filename
    

    #insertBook(param1)
    #cursor.execute('INSERT INTO Book (Book_ID) VALUES (?)', (column1_value))
    # Insert the data into the SQLite table
    
    try:
        validate_email(param1)
        validate_password(param2)
        validate_picture(file)
        
        
        current_date = date.today()
        formatted_date = current_date.strftime("%Y%m%d")
        #print(date1)
        file_path = os.path.join('pic',formatted_date)
        file.save(file_path)
        
        cursor.execute("INSERT INTO login (email, password, is_admin, img) VALUES (?, ?, ?, ?)",
                   (param1, param2, param3, file_path))
    #print(name)

        conn.commit()
        conn.close()

        return 'Data inserted successfully!'
    
    except Exception  as e:
        return jsonify({'error': str(e)}), 400







def validate_email(email):
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise ValueError('Invalid email format!')




def validate_password(password):
    if len(password) < 8:
        raise ValueError('Password must be at least 8 characters long')
    # Add additional password validation rules as needed



def validate_picture(picture):
    if not picture:
        raise Exception("Insert the Picture")
        
    if not picture.filename.endswith(('.jpg', '.jpeg', '.png')):
           raise Exception("Invalid picture format")
    

@app.route('/result', methods=['GET'])
def handle_get():
    conn = connect()
    cursor = conn.cursor()

    # Retrieve data from the SQLite table
    cursor.execute("SELECT * FROM login")
    rows = cursor.fetchall()
   
    # Convert the rows to a list of dictionaries
    data = []
    for row in rows:
        data.append({
            'email': row[0],
            'password': row[1],
            'is_admin': row[2],
            'picture': row[3]
            
        })

    conn.close()

    return jsonify(data)













def authenticate(username, password):
    conn = sqlite3.connect('database5.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM login WHERE email=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user




'''
def create_random_token(token_length):
    token = secrets.token_hex(token_length)
    return token
'''
# Example usage




@app.route('/protected', methods=['GET'])
def protected_resource():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'No token provided'})

    token = token.split()[1]  # Remove "Bearer " prefix

    user_id = verify_token(token)
    if isinstance(user_id, str):
        return jsonify({'error': user_id})

    # Access the protected resource
    # Your logic goes here

    return jsonify({'message': 'Protected resource accessed'})


@app.route('/login', methods=['POST'])
def login():
    #data = request.get_json()
    username =  request.json.get('username')#request.form.get('Email')
    password =  request.json.get('password')#request.form.get('password')
   


    user = authenticate(username, password)
    
    if user:
        # Successful login
        
     
        random_token = generate_token(username)
        #update_data(random_token, user[0])
        response = {
            'Message': 'Login successful',
            'Is Admin': 'Yes' if user[2]==0 else 'No',
            'Token': random_token
        }   
 
        return jsonify(response), 200
    else:
        # Invalid credentials
        response = {
            'message': 'Invalid username or password'
        }
        return jsonify(response), 401



def update_data(newtoken, username):
    # Establish a connection to the SQLite database
    conn = sqlite3.connect('database5.db')
    cursor = conn.cursor()

    # Construct the SQL UPDATE statement
    update_query = '''
        UPDATE login
        SET token = ? 
        WHERE email = ?;
    '''    
        
    #cursor.execute('update from login set token = ? w * from Book where {} = book_id'.format(bookid))

    # Execute the UPDATE statement
    cursor.execute(update_query, (newtoken, username))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()





def token(username):
    conn = sqlite3.connect('database5.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM login WHERE email=? ", (username,))
    user = cursor.fetchone()
    conn.close()
    return user


def search(token):
    conn = sqlite3.connect('database5.db')
    cursor = conn.cursor()
    search_query = ''' select email, is_admin from login where token = ?'''
    cursor.execute(search_query,(token,))
    result = cursor.fetchall()
    return result
    
@app.route('/info', methods=['GET'])
def info():
    data = request.get_json()
    token = data.get('token')
    user = search(token)

    if user:
        response = {
            'Message': 'Login successful',
            'User Name': user[0][0],
            'Is Admin': 'Yes' if user[0][1]==1 else 'No'
        }
        return jsonify(response), 200
        
    else:
        response = {
                'message': 'User not found'
            }
        return jsonify(response), 404
    
    

        
    

    
def delete(token):
    conn = sqlite3.connect('database5.db')
    cursor = conn.cursor()
    delete_query = ''' DELETE FROM login WHERE token = ?'''
    cursor.execute(delete_query,(token,))
    
    
@app.route('/logout', methods=['POST'])
def logout():
    data = request.get_json()
    token = data.get('token')
    user = search(token)
    if user:
        delete(token)
        response = {
                'message': 'The User is Logout'
            }
        return jsonify(response), 200
        
    else:
        
       response = {
               'message': 'User not found'
           }
       return jsonify(response), 404




if __name__ == '__main__':
    app.run()