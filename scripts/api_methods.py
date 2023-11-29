import datetime
from flask import redirect, render_template, session, url_for
import hashlib
import os
import main
    
def generate_html_response(response_messages):
    # Dynamic content for the table
    table_content = ""
    for message in response_messages:
        table_content += f"<tr><td>{message['CompanyName']}</td><td>{message['FKZ']}</td></tr>"

    return render_template('response.html', table_content=table_content)

def hash_password(password):
    # Hash the password using a secure hashing algorithm (e.g., SHA-256)
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return hashed_password

def store_credentials(username, password):
    # Hash the password before storing it in the database
    hashed_password = hash_password(password)

    # Store the username and hashed password in the Oracle table
    query = "INSERT INTO API_USERS_2 (username, password_hash) VALUES (:username, :password_hash)"
    main.cursor.executeSQL(query, {'username': username, 'password_hash': hashed_password})

def check_credentials(username, password):
    # Hash the provided password for comparison with the stored hashed password
    hashed_password_attempt = hash_password(password)

    # Fetch the hashed password from the database for the given username
    query = "SELECT password_hash FROM API_USERS_2 WHERE username = :username"
    stored_password_hash = main.cursor.getScalarResult(query, {'username': username})

    if stored_password_hash and hashed_password_attempt == stored_password_hash:
        return True
    return False

def is_valid_date(date_string, date_format="%d.%m.%y"):
    try:
        # Attempt to parse the date using the specified format
        datetime.datetime.strptime(date_string, date_format)
        return True
    except ValueError:
        return False
    
def check_dates(data):
    date_fields = ['LAUFZEITBEGINN', 'LAUFZEITENDE', 'BEWILLIGUNGSDATUM', 'FOUNDEDDATE']
    invalid_dates = []

    for entry in data:
        for field in date_fields:
            if field not in entry:
                continue

            date_value = entry[field]
            if not is_valid_date(date_value):
                invalid_dates.append(f"{field} in entry {entry}")

    if invalid_dates:
        message = f"Invalid dates in fields: {', '.join(invalid_dates)}"
        return False, message
    else:
        return True, None
    
