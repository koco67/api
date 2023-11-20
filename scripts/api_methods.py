import datetime
from flask import redirect, render_template, session, url_for
import main

    
def generate_html_response(response_messages):
    # Dynamic content for the table
    table_content = ""
    for message in response_messages:
        table_content += f"<tr><td>{message['CompanyName']}</td><td>{message['FKZ']}</td></tr>"

    return render_template('response.html', table_content=table_content)

def check_credentials(username, password):
    query = "SELECT password FROM API_USERS WHERE username = :username"
    result = main.cursor.getScalarResult(query, {'username': username})
    if result == password:
        return True
    else:
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
    