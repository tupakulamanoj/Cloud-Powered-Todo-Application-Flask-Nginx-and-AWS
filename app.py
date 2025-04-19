import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', '')

# MySQL Configuration
db_config = {
    'host': os.environ.get('DB_HOST', ""),
    'user': os.environ.get('DB_USER', 'admin'),
    'password': os.environ.get('DB_PASSWORD', 'Manoj2025'),
    'db': os.environ.get('DB_NAME', 'flask_todo'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if user:
                return User(user['id'], user['username'])
    finally:
        connection.close()
    return None

def get_db_connection():
    return pymysql.connect(**db_config)

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('todos'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Form validation
        if not username or not password or not confirm_password:
            flash('All fields are required')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register'))
        
        # Hash the password
        hashed_password = generate_password_hash(password)
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # Check if username already exists
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    flash('Username already exists')
                    return redirect(url_for('register'))
                
                # Insert new user
                cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", 
                              (username, hashed_password))
                connection.commit()
                
                # Get the user for login
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                user_obj = User(user['id'], user['username'])
                login_user(user_obj)
                
                flash('Registration successful!')
                return redirect(url_for('todos'))
        except Exception as e:
            flash(f'An error occurred: {str(e)}')
            return redirect(url_for('register'))
        finally:
            connection.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                
                if user and check_password_hash(user['password'], password):
                    user_obj = User(user['id'], user['username'])
                    login_user(user_obj)
                    flash('Login successful!')
                    return redirect(url_for('todos'))
                else:
                    flash('Invalid username or password')
                    return redirect(url_for('login'))
        finally:
            connection.close()
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('index'))

@app.route('/todos')
@login_required
def todos():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM todos WHERE user_id = %s ORDER BY created_at DESC", 
                          (current_user.id,))
            todos = cursor.fetchall()
            return render_template('todos.html', todos=todos)
    finally:
        connection.close()

@app.route('/add_todo', methods=['POST'])
@login_required
def add_todo():
    title = request.form['title']
    description = request.form['description']
    
    if not title:
        flash('Title is required')
        return redirect(url_for('todos'))
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO todos (user_id, title, description) VALUES (%s, %s, %s)",
                          (current_user.id, title, description))
            connection.commit()
            flash('Todo added successfully!')
    except Exception as e:
        flash(f'An error occurred: {str(e)}')
    finally:
        connection.close()
    
    return redirect(url_for('todos'))

@app.route('/complete_todo/<int:todo_id>')
@login_required
def complete_todo(todo_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Verify todo belongs to current user
            cursor.execute("SELECT * FROM todos WHERE id = %s AND user_id = %s", 
                          (todo_id, current_user.id))
            todo = cursor.fetchone()
            
            if todo:
                # Toggle the completed status
                new_status = not todo['completed']
                cursor.execute("UPDATE todos SET completed = %s WHERE id = %s", 
                              (new_status, todo_id))
                connection.commit()
                flash('Todo status updated')
            else:
                flash('Todo not found or unauthorized')
    finally:
        connection.close()
    
    return redirect(url_for('todos'))

@app.route('/delete_todo/<int:todo_id>')
@login_required
def delete_todo(todo_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Verify todo belongs to current user
            cursor.execute("SELECT * FROM todos WHERE id = %s AND user_id = %s", 
                          (todo_id, current_user.id))
            todo = cursor.fetchone()
            
            if todo:
                cursor.execute("DELETE FROM todos WHERE id = %s", (todo_id,))
                connection.commit()
                flash('Todo deleted successfully!')
            else:
                flash('Todo not found or unauthorized')
    finally:
        connection.close()
    
    return redirect(url_for('todos'))

if __name__ == '__main__':
    app.run(debug=True)
