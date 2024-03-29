import csv
import datetime
import io
import json
from flask import Flask, Response, request, jsonify, redirect, send_file, send_from_directory, session, url_for, render_template, flash
from profi_control import ProfiControl
from stdArgParser import getStandardArgParser
from status import Status
import api_methods
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'key'
parser = getStandardArgParser()
args = parser.parse_args()
cursor = ProfiControl(args.oracleUser, args.oraclePassword, args.saveCredentials, args.setDefaultUser)
status = Status()




# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

# Login page
@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        if api_methods.check_credentials(username, password):
            session['username'] = username  # Store the username in the session
            return redirect(url_for('upload_row'))
        else:
            status.setStatus(401, "INCORRECT_LOGIN")
    return render_template('login.html')

@app.route('/sign-out', methods=['POST'])
def sign_out():
    
    session.pop('username', None)
    return render_template('login.html')

# up
@app.route("/upload-row", methods=["GET", "POST"])
def upload_row():
    session['temp_csv_content'] = []

    if 'username' not in session:
        status.setStatus(401, "INCORRECT_LOGIN")
        return render_template('login.html')

        
    if request.method == "POST":
        if 'file' not in request.files:
            status.setStatus(401, "NO_FILE")
        
        file = request.files['file']

        if file.filename == '':
            status.setStatus(401,"NO_FILE_SELECTED")
            return render_template('upload_row.html')

        current_date = datetime.date.today().strftime("%d.%m.%Y")

        try:

            if file:
                if file.filename.endswith('.csv'):
                    with io.TextIOWrapper(file.stream, encoding='utf-8') as text_file:
                        reader = csv.DictReader(text_file)
                        header = [key.upper() for key in reader.fieldnames]  # Get the header row and convert keys to uppercase
                        new_reader = [{key.upper(): value.strip() if isinstance(value, str) else value for key, value in entry.items()} for entry in reader]

                        session['temp_csv_content'].clear()

                        if all(key in header for key in ["VERBUNDBEZEICHNUNG", "THEMA", "LAUFZEITBEGINN", "LAUFZEITENDE", "BEWILLIGUNGSDATUM", "BEWILLIGUNGSSUMME", "COMPANYNAME", "FOUNDEDDATE", "URL", "EMAIL", "TEL", "STREET", "ZIPCODE", "CITY", "DESCRIPTION"]):

                            is_valid, error_message = api_methods.check_dates(new_reader)
                            if not is_valid:
                            # Handle the error condition, e.g., flash the error message or return an error response
                                flash(error_message, 'error')
                                return redirect(url_for('upload_row'))
                            
                            response_messages = []  # Collect response messages for each row
                     
                            for row in new_reader:
                                #row = {key: value.strip() if isinstance(value, str) else value for key, value in row.items()}
                                query = "select count(*) + 1 from company where fkz like '03EEXT%'"
                                current_fkz_number = cursor.getScalarResult(query,None)
                                fkz_value = f"03EEXT{current_fkz_number:04d}"
                                akz_value = fkz_value[3:]  
                                #row = {key.upper(): value for key, value in row.items()}
                                
                                query = "INSERT INTO COMPANY (FKZ, AKZ, ACTIVE, COMPANYNAME, FOUNDEDDATE, URL, EMAIL, TEL, STREET, ZIPCODE, CITY, DESCRIPTION) VALUES (:FKZ, :AKZ, :ACTIVE, :COMPANYNAME, :FOUNDEDDATE, :URL, :EMAIL, :TEL, :STREET, :ZIPCODE, :CITY, :DESCRIPTION)"
                                cursor.executeSQL(query, {'FKZ': fkz_value, 'AKZ': akz_value, 'ACTIVE': 1, 'COMPANYNAME': row['COMPANYNAME'], 'FOUNDEDDATE': row['FOUNDEDDATE'], 'URL': row['URL'], 'EMAIL': row['EMAIL'], 'TEL': row['TEL'], 'STREET': row['STREET'], 'ZIPCODE': row['ZIPCODE'], 'CITY': row['CITY'], 'DESCRIPTION': row['DESCRIPTION']})
                            
                                query = "INSERT INTO I_PROFI_GRUNDDATEN (FKZ, AKRONYM, EINGANGSDATUM, VERBUNDBEZEICHNUNG, THEMA, LAUFZEITBEGINN, LAUFZEITENDE, BEWILLIGUNGSDATUM, BEWILLIGUNGSSUMME) VALUES (:FKZ, :AKRONYM, :EINGANGSDATUM, :VERBUNDBEZEICHNUNG, :THEMA, :LAUFZEITBEGINN, :LAUFZEITENDE, :BEWILLIGUNGSDATUM, :BEWILLIGUNGSSUMME)"
                                cursor.executeSQL(query, {'FKZ': fkz_value, 'AKRONYM': row['COMPANYNAME'], 'EINGANGSDATUM': current_date, 'VERBUNDBEZEICHNUNG': row['VERBUNDBEZEICHNUNG'], 'THEMA': row['THEMA'], 'LAUFZEITBEGINN': row['LAUFZEITBEGINN'], 'LAUFZEITENDE': row['LAUFZEITENDE'], 'BEWILLIGUNGSDATUM': row['BEWILLIGUNGSDATUM'], 'BEWILLIGUNGSSUMME': row['BEWILLIGUNGSSUMME']})
                            
                                response_messages.append({"FKZ": fkz_value, "CompanyName": row['COMPANYNAME']})
                                session['temp_csv_content'].append({'FKZ': fkz_value, 'AKZ': akz_value, 'ACTIVE': 1, 'COMPANYNAME': row['COMPANYNAME'], 'FOUNDEDDATE': row['FOUNDEDDATE'], 'URL': row['URL'], 'EMAIL': row['EMAIL'], 'TEL': row['TEL'], 'STREET': row['STREET'], 'ZIPCODE': row['ZIPCODE'], 'CITY': row['CITY'], 'DESCRIPTION': row['DESCRIPTION'], 'AKRONYM': row['COMPANYNAME'], 'EINGANGSDATUM': current_date, 'VERBUNDBEZEICHNUNG': row['VERBUNDBEZEICHNUNG'], 'THEMA': row['THEMA'], 'LAUFZEITBEGINN': row['LAUFZEITBEGINN'], 'LAUFZEITENDE': row['LAUFZEITENDE'], 'BEWILLIGUNGSDATUM': row['BEWILLIGUNGSDATUM'], 'BEWILLIGUNGSSUMME': row['BEWILLIGUNGSSUMME']})

                                html_response = api_methods.generate_html_response(response_messages)

                            return html_response, 200
                        else:
                            return jsonify({"error": "Missing or incorrect keys in csv file, please view examples for more information"}), 400
            
                elif file.filename.endswith('.json'):
                    data = json.loads(file.read())

                    #new_data = [{key.upper(): value for key, value in entry.items()} for entry in data]
                    new_data = [{key.upper(): value.strip() if isinstance(value, str) else value for key, value in entry.items()} for entry in data]
                    session['temp_csv_content'].clear()

                    if all(key.upper() in new_data[0] for key in ["VERBUNDBEZEICHNUNG", "THEMA", "LAUFZEITBEGINN", "LAUFZEITENDE", "BEWILLIGUNGSDATUM", "BEWILLIGUNGSSUMME", "COMPANYNAME", "FOUNDEDDATE", "URL", "EMAIL", "TEL", "STREET", "ZIPCODE", "CITY", "DESCRIPTION"]):
                        is_valid, error_message = api_methods.check_dates(new_data)
                        if not is_valid:
                            # Handle the error condition, e.g., flash the error message or return an error response
                            flash(error_message, 'error')
                            return redirect(url_for('upload_row'))
                        else:
                            response_messages = []  # Collect response messages for each row

                            for row in new_data:
                                query = "select count(*) + 1 from company where fkz like '03EEXT%'"
                                current_fkz_number = cursor.getScalarResult(query,None)
                                fkz_value = f"03EEXT{current_fkz_number:04d}"
                                akz_value = fkz_value[3:] 

                                query = "INSERT INTO COMPANY (FKZ, AKZ, ACTIVE, COMPANYNAME, FOUNDEDDATE, URL, EMAIL, TEL, STREET, ZIPCODE, CITY, DESCRIPTION) VALUES (:FKZ, :AKZ, :ACTIVE, :COMPANYNAME, :FOUNDEDDATE, :URL, :EMAIL, :TEL, :STREET, :ZIPCODE, :CITY, :DESCRIPTION)"
                                cursor.executeSQL(query, {'FKZ': fkz_value, 'AKZ': akz_value, 'ACTIVE': 1, 'COMPANYNAME': row['COMPANYNAME'], 'FOUNDEDDATE': row['FOUNDEDDATE'], 'URL': row['URL'], 'EMAIL': row['EMAIL'], 'TEL': row['TEL'], 'STREET': row['STREET'], 'ZIPCODE': row['ZIPCODE'], 'CITY': row['CITY'], 'DESCRIPTION': row['DESCRIPTION']})
                                
                                query = "INSERT INTO I_PROFI_GRUNDDATEN (FKZ, AKRONYM, EINGANGSDATUM, VERBUNDBEZEICHNUNG, THEMA, LAUFZEITBEGINN, LAUFZEITENDE, BEWILLIGUNGSDATUM, BEWILLIGUNGSSUMME) VALUES (:FKZ, :AKRONYM, :EINGANGSDATUM, :VERBUNDBEZEICHNUNG, :THEMA, :LAUFZEITBEGINN, :LAUFZEITENDE, :BEWILLIGUNGSDATUM, :BEWILLIGUNGSSUMME)"
                                cursor.executeSQL(query, {'FKZ': fkz_value, 'AKRONYM': row['COMPANYNAME'], 'EINGANGSDATUM': current_date, 'VERBUNDBEZEICHNUNG': row['VERBUNDBEZEICHNUNG'], 'THEMA': row['THEMA'], 'LAUFZEITBEGINN': row['LAUFZEITBEGINN'], 'LAUFZEITENDE': row['LAUFZEITENDE'], 'BEWILLIGUNGSDATUM': row['BEWILLIGUNGSDATUM'], 'BEWILLIGUNGSSUMME': row['BEWILLIGUNGSSUMME']})
                                
                                response_messages.append({"FKZ": fkz_value, "CompanyName": row['COMPANYNAME']})
                                session['temp_csv_content'].append({'FKZ': fkz_value, 'AKZ': akz_value, 'ACTIVE': 1, 'COMPANYNAME': row['COMPANYNAME'], 'FOUNDEDDATE': row['FOUNDEDDATE'], 'URL': row['URL'], 'EMAIL': row['EMAIL'], 'TEL': row['TEL'], 'STREET': row['STREET'], 'ZIPCODE': row['ZIPCODE'], 'CITY': row['CITY'], 'DESCRIPTION': row['DESCRIPTION'], 'AKRONYM': row['COMPANYNAME'], 'EINGANGSDATUM': current_date, 'VERBUNDBEZEICHNUNG': row['VERBUNDBEZEICHNUNG'], 'THEMA': row['THEMA'], 'LAUFZEITBEGINN': row['LAUFZEITBEGINN'], 'LAUFZEITENDE': row['LAUFZEITENDE'], 'BEWILLIGUNGSDATUM': row['BEWILLIGUNGSDATUM'], 'BEWILLIGUNGSSUMME': row['BEWILLIGUNGSSUMME']})

                                html_response = api_methods.generate_html_response(response_messages)

                        return html_response, 200
                    else:
                        return jsonify({"error": "Missing or incorrect keys in json file, please view examples for more information"}), 400
        
                    
                else:
                    return jsonify({"error": "Unsupported file format"}), 400

        except Exception as e:
            return jsonify({"error": str(e)}), 400
        
    return render_template('upload_row.html')


@app.route('/example-page')
def example_page():
    return render_template('example_page.html')


@app.route('/change-password', methods=['GET'])
def change_password_page():
    if 'username' not in session:
        status.setStatus(401, "INCORRECT_LOGIN")
        return render_template('login.html')
    return render_template('change_password.html')

@app.route('/change-password', methods=['POST'])
def change_password():
    if 'username' not in session:
        status.setStatus(401, "INCORRECT_LOGIN")
        return render_template('login.html')
    
    # Get the old and new passwords from the form
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')

    # Check if the current password is correct
    if api_methods.check_credentials(session.get('username'), current_password):
        # Update the password in the database
        query = "UPDATE API_USERS SET password_hash = :new_password WHERE username = :username"
        cursor.executeSQL(query, {'new_password': api_methods.hash_password(new_password), 'username': session.get('username')})

        flash('Password changed successfully!', 'success')
    else:
        flash('Incorrect current password. Password not changed.', 'error')

    #return render_template('login.html')
    return render_template('upload_row.html')



@app.route('/download-json')
def download_json():
    json_data = [
        {
            "VERBUNDBEZEICHNUNG": "AAAVERBUNDBEZEICHNUNG1",
            "THEMA": "thema1",
            "LAUFZEITBEGINN": "01.10.23",
            "LAUFZEITENDE": "30.09.24",
            "BEWILLIGUNGSDATUM": "23.08.07",
            "BEWILLIGUNGSSUMME": "122317,08",
            "COMPANYNAME": "AAACompany1",
            "FOUNDEDDATE": "05.04.19",
            "URL": "www.probe.com",
            "EMAIL": "email.com",
            "TEL": "12356789",
            "STREET": "street 1",
            "ZIPCODE": "12345",
            "CITY": "Berlin",
            "DESCRIPTION": "this is a company..."
        },
        {
            "VERBUNDBEZEICHNUNG": "AAAVERBUNDBEZEICHNUNG1",
            "THEMA": "thema1",
            "LAUFZEITBEGINN": "01.10.23",
            "LAUFZEITENDE": "30.09.24",
            "BEWILLIGUNGSDATUM": "23.08.07",
            "BEWILLIGUNGSSUMME": "122317,08",
            "COMPANYNAME": "AAACompany1",
            "FOUNDEDDATE": "05.04.19",
            "URL": "www.probe.com",
            "EMAIL": "email.com",
            "TEL": "12356789",
            "STREET": "street 1",
            "ZIPCODE": "12345",
            "CITY": "Berlin",
            "DESCRIPTION": "this is a company..."
        }
    ]

    # Create a Flask Response object with JSON data
    response = Response(response=json.dumps(json_data), status=200, mimetype='application/json')
    
    # Set the content-disposition header to trigger a download
    response.headers['Content-Disposition'] = 'attachment; filename=example.json'

    return response

@app.route('/download-csv')
def download_csv():
    example_data = [
        {"VERBUNDBEZEICHNUNG": "AAAVERBUNDBEZEICHNUNG1", "THEMA": "thema1", "LAUFZEITBEGINN": "01.10.23", "LAUFZEITENDE": "30.09.24", "BEWILLIGUNGSDATUM": "23.08.07", "BEWILLIGUNGSSUMME": "\"122317,08\"", "COMPANYNAME": "AAACompany1", "FOUNDEDDATE": "05.04.19", "URL": "www.probe.com", "EMAIL": "email.com", "TEL": "12356789", "STREET": "street 1", "ZIPCODE": "12345", "CITY": "Berlin", "DESCRIPTION": "this is a company..."},
        {"VERBUNDBEZEICHNUNG": "AAAVERBUNDBEZEICHNUNG1", "THEMA": "thema1", "LAUFZEITBEGINN": "01.10.23", "LAUFZEITENDE": "30.09.24", "BEWILLIGUNGSDATUM": "23.08.07", "BEWILLIGUNGSSUMME": "\"122317,08\"", "COMPANYNAME": "AAACompany1", "FOUNDEDDATE": "05.04.19", "URL": "www.probe.com", "EMAIL": "email.com", "TEL": "12356789", "STREET": "street 1", "ZIPCODE": "12345", "CITY": "Berlin", "DESCRIPTION": "this is a company..."}
    ]

    csv_content = "VERBUNDBEZEICHNUNG,THEMA,LAUFZEITBEGINN,LAUFZEITENDE,BEWILLIGUNGSDATUM,BEWILLIGUNGSSUMME,COMPANYNAME,FOUNDEDDATE,URL,EMAIL,TEL,STREET,ZIPCODE,CITY,DESCRIPTION\n"
    for row in example_data:
        csv_content += ','.join(map(str, row.values())) + '\n'

    response = Response(csv_content, content_type='text/csv')
    response.headers["Content-Disposition"] = "attachment; filename=example.csv"
    return response

@app.route("/download-uploaded-data")
def download_uploaded_data():

    csv_content = "FKZ, AKZ, ACTIVE, COMPANYNAME, FOUNDEDDATE, URL, EMAIL, TEL, STREET, ZIPCODE, CITY, DESCRIPTION, AKRONYM, EINGANGSDATUM, VERBUNDBEZEICHNUNG, THEMA, LAUFZEITBEGINN, LAUFZEITENDE, BEWILLIGUNGSDATUM, BEWILLIGUNGSSUMME\n"
    for row in session['temp_csv_content']:
        # Explicitly define the order of columns
        ordered_values = [
            row['FKZ'],
            row['AKZ'],
            row['ACTIVE'],
            row['COMPANYNAME'],
            row['FOUNDEDDATE'],
            row['URL'],
            row['EMAIL'],
            row['TEL'],
            row['STREET'],
            row['ZIPCODE'],
            row['CITY'],
            row['DESCRIPTION'],
            row['AKRONYM'],
            row['EINGANGSDATUM'],
            row['VERBUNDBEZEICHNUNG'],
            row['THEMA'],
            row['LAUFZEITBEGINN'],
            row['LAUFZEITENDE'],
            row['BEWILLIGUNGSDATUM'],
            row['BEWILLIGUNGSSUMME']
        ]
        csv_content += ','.join(map(str, ordered_values)) + '\n'
    response = Response(csv_content, content_type='text/csv')
    response.headers["Content-Disposition"] = "attachment; filename=uploaded.csv"
    session['temp_csv_content'].clear()
    return response

if __name__ == '__main__':
    
    parser = getStandardArgParser()
    args = parser.parse_args()
    app.run(debug=True)


