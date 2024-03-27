# Import necessary modules and packages
from flask import Blueprint, render_template, request, redirect, url_for, flash,current_app,g,session, jsonify
import os
from io import BytesIO
import sqlite3
import base64
from datetime import datetime
import logging
import json


home_blueprint = Blueprint('home', __name__)
logger_file = logging.getLogger("error.log")

# Function to establish database connection
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('assignmentdb.db')
        g.cursor = g.db.cursor()
    return g.db, g.cursor

def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Route for displaying room gallery
@home_blueprint.route('/gallery', methods=['GET', 'POST'])
def room_gallery():
    db,cursor = get_db()
    username = session.get('username')

    cursor.execute("SELECT * FROM rooms")
    rooms = cursor.fetchall()
    updated_rooms = []
    user_type = session.get('user_type')
    for room in rooms:
        image_blob = room[4]
        encoded_image = base64.b64encode(image_blob).decode('utf-8')
        updated_room = list(room) + [encoded_image]
        updated_rooms.append(updated_room)

    image_folder = os.path.join(current_app.root_path, 'static') + '/images/'
    image_filenames = [f for f in os.listdir(image_folder) if f.endswith(('.png', '.jpg', '.jpeg'))]

    return render_template('gallery.html', rooms=updated_rooms, username=username, user_type=user_type, image_filenames=image_filenames, image_folder=image_folder)
 
# Route for viewing individual rooms
@home_blueprint.route('/rooms/<room_name>', methods=['GET', 'POST'])
def viewing_rooms(room_name):
    user_type = request.args.get('user_type')
    image_folder = os.path.join(current_app.root_path, 'static')+'/images/' +str(room_name)
    image_filenames = [f for f in os.listdir(image_folder) if f.endswith(('.png', '.jpg', '.jpeg'))]
    slide_range = range(1, len(image_filenames) + 1)
    return render_template('viewing.html', image_filenames=image_filenames,image_folder=image_folder, room_name = room_name, slide_range=slide_range, user_type = user_type)


# Route for submitting room booking
@home_blueprint.route('/book_room', methods=['POST'])
def submit_room():
    try:
        db,cursor = get_db()
        room_name = request.form['room_name']
        username = session.get('username')
        date = (request.form.get('date'))
        current_format_obj = datetime.strptime((request.form.get('date')), '%Y-%m-%d')
        date = (current_format_obj.strftime('%d/%m/%Y'))
        time = request.form['time']
        attendance = request.form['attendance']
        equipment = request.form['equipment'] or None
        status = 'Booked'

        cursor.execute("""
                INSERT INTO booking (room_name, userID, date, time, attendance, equipment, status)
                VALUES (?,?, ?, ?, ?, ?, ?)
            """.format(), (room_name,username,date, time, attendance, equipment, status))
        
        db.commit()
        message = f"alert('Booking Successful');"
        return f"<script>{message} window.location.href = '{url_for('home.user_booking', username=username)}';</script>"
    
    except Exception as e:
        current_app.logger.info('Couldnt book room')


# Route for displaying user bookings
@home_blueprint.route('/<username>/bookings', methods=['GET', 'POST'])
def user_booking(username):
    db, cursor = get_db()

    username = session.get('username')
    name = session.get('name')
    today_str = datetime.now().strftime('%d/%m/%Y')

    cursor.execute("SELECT * FROM booking WHERE userID = ? AND status == 'Booked' AND date >= ? ORDER BY date ASC", (username,today_str))
    bookings = cursor.fetchall()

    close_db(None)
    return render_template('user_bookings.html', username=username, bookings=bookings, name=name)

# Route for cancelling room bookings
@home_blueprint.route('/cancel_rooms', methods=['GET', 'POST'])
def cancel_booking():
    booking_id = request.form.get('booking_id')
    user_type = request.form.get('user_type')
    db,cursor = get_db()
    cancellation_reason = f'Cancelled by {user_type.capitalize()}' 
    try:
        cursor.execute("UPDATE booking SET status = '{}' WHERE bookingID = ?".format(cancellation_reason), (booking_id,))
        db.commit()

    except:
        current_app.logger.info('Couldnt delete')
    return redirect(url_for('home.user_booking', username=session.get('username')))

# Route for updating room bookings
@home_blueprint.route('/update_bookings', methods=['GET', 'POST'])
def update_booking():
    db,cursor = get_db()
    booking_id = request.form.get('booking_id')
    date = request.form.get('date')
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    date = date_obj.strftime('%d/%m/%Y')
    time = request.form.get('time')
    attendance = request.form.get('attendance')
    equipment = request.form.get('equipment')

    try:
        cursor.execute("""
            UPDATE booking
            SET date = ?, time = ?, attendance = ?, equipment = ?
            WHERE bookingID = ?
        """, (date, time, attendance, equipment, booking_id))
        db.commit()

    except:
        current_app.logger.info('Couldnt update')

    return redirect(url_for('home.user_booking', username=session.get('username')))
