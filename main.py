# Import necessary modules and packages
from flask import Flask, render_template,session, request, redirect, url_for, flash,Blueprint
from werkzeug.security import generate_password_hash, check_password_hash
from home import home_blueprint, room_gallery, get_db
from admin import admin_blueprint,admin_home

import sqlite3

# Create a Flask application instance
app = Flask(__name__, static_folder='static\\')
app.secret_key = 'strong_key'
app.register_blueprint(home_blueprint)
app.register_blueprint(admin_blueprint)

# List of security questions for user registration and recovery
security_questions = [
    "What is your mother's maiden name?",
    "What city were you born in?",
    "What is the name of your first pet?",
    "What is your favorite food?",
    "What is the make and model of your first car?"
]

# Route for the home page, redirects to the login page
@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect(url_for('login'))

# Route for user login functionality
@app.route('/login', methods=['GET', 'POST'])
def login():

    conn = sqlite3.connect('assignmentdb.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        emailaddress = request.form['emailaddress']
        password = request.form['password']
        user_type = request.form['login_type']

        if user_type == 'user':

            try:
                cursor.execute('SELECT userID,password,name FROM user WHERE email = ? and status = "Active"', (emailaddress,))
                result = cursor.fetchone()
                if result:
                    hashed_password = result[1]
                    if check_password_hash(hashed_password, password):
                        flash('Login successful!', 'success')
                        session['email'] = emailaddress
                        session['username'] = result[0]
                        session['name'] = result[2]

                        session['user_type'] = 'regular'
                        session['logged_in'] = True
                        return redirect(url_for('home.room_gallery'))
                    else:
                        flash('Invalid email or password', 'error')
                        return redirect(url_for('login'))
                else:
                    flash('Invalid email or password', 'error')
                    return redirect(url_for('login'))
                
            except:
                return redirect(url_for('login'))

            
        if user_type == 'admin':

            try:
                cursor.execute('SELECT password FROM admin WHERE email = ? and status = "Active"', (emailaddress,))
                result = cursor.fetchone()
                if result:
                    hashed_password = result[0]
                    if check_password_hash(hashed_password, password):
                        flash('Login successful!', 'success')  
                        session['user_type'] = 'admin'
                        session['username'] = result[0]
                        session['logged_in'] = True
                        return redirect(url_for('admin.admin_home'))
                    else:
                        flash('Invalid username or password', 'error')  
                        return redirect(url_for('login'))
                else:
                    flash('Invalid email or password', 'error') 
                    return redirect(url_for('login'))
                
            except:
                return redirect(url_for('login'))

    return render_template('login.html', security_questions=security_questions)

# Route for user signup functionality
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':

        db, cursor = get_db()

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        recovery_question = request.form['security_question']
        recovery_answer = request.form['security_answer']
        status = 'Active'

    cursor.execute("""
            INSERT INTO user (password, recoveryQuestion,recoveryAnswer, name,email, status )
            VALUES (?,?, ?,?,?,?)
        """.format(), (generate_password_hash(password), recovery_question, recovery_answer,name, email, status))
    
    db.commit()

    return render_template('login.html', security_questions=security_questions)

# Route for handling forgot password functionality
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':

        db, cursor = get_db()

        email = request.form['email']
        recovery_question = request.form['security_question']
        recovery_answer = request.form['security_answer']

        cursor.execute("SELECT * FROM user WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user:
            stored_recovery_question = user[2]
            stored_recovery_answer = user[3]

            if recovery_question == stored_recovery_question and recovery_answer == stored_recovery_answer:
                user_authentication = 'true'
            
                return render_template('login.html', user_authentication = user_authentication, reset_email = email)

            else:
                user_authentication = 'false'
                
                return render_template('login.html', user_authentication = user_authentication, security_questions=security_questions)
            
        else: 
            user_authentication = 'false'
            return render_template('login.html', user_authentication = user_authentication, security_questions=security_questions)


# Route for handling password reset functionality
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        db, cursor = get_db()
        new_password = request.form['new_password']
        confirm_new_password = request.form['confirm_new_password']
        reset_email = request.form['email']

        cursor.execute("UPDATE user SET password = '{}' WHERE email = ?".format(generate_password_hash(new_password)), (reset_email,))
        db.commit()

        reset_done ='true'
        return render_template('login.html', security_questions=security_questions, reset_done = reset_done)


# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
