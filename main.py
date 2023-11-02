import json
from flask import Flask, request, jsonify, redirect, url_for, render_template
import cx_Oracle
from oracledb import IntegrityError

app = Flask(__name__)
serviceName_attr = 'FZJA.FZJ.DE'
sid = 'FZJA'
url_attr = 'ORASRV.ZAM.KFA-JUELICH.DE'
port_attr = 1521
clientDirectory_attr = \
            r'c:\Users\dhamik\Desktop\instantclient_19_6'
try:  # in case Ora Client lib has already been initialized
    cx_Oracle.init_oracle_client(lib_dir=clientDirectory_attr)
except Exception:
    pass
#normalerweise serviceName statt sid
dsn_tns = cx_Oracle.makedsn(url_attr,port_attr,sid)
connection = cx_Oracle.connect(user='gtiprofiaccess', password = 'iP#5SsxuG3', dsn=dsn_tns)
cursor = connection.cursor()

# Function to check credentials
def check_credentials(username, password):
    query = "SELECT password FROM API_USERS WHERE username = :username"
    cursor.execute(query, {'username': username})
    result = cursor.fetchone()
    if result and result[0] == password:
        return True
    else:
        return False

# Login page
@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        if check_credentials(username, password):
            return redirect(url_for('update_row'))
        else:
            return "Username or password is incorrect"

    return render_template('login.html')

@app.route("/update-row", methods=["GET", "POST"])
def update_row():
    if request.method == "POST":
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400#
        
        file = request.files['file']

        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        try:
            if file:
                data = json.loads(file.read())
                if all(key in data[0] for key in ["FKZ", "verbundbezeichnung", "THEMA", "LAUFZEITBEGINN", "LAUFZEITENDE", "BEWILLIGUNGSDATUM", "BEWILLIGUNGSSUMME"]):
                    # Insert the first 6 fields into one table
                    for row in data:
                        query = "INSERT INTO I_PROFI_GRUNDDATEN (FKZ, verbundbezeichnung, THEMA, LAUFZEITBEGINN, LAUFZEITENDE, BEWILLIGUNGSDATUM, BEWILLIGUNGSSUMME) VALUES (:FKZ, :verbundbezeichnung, :THEMA, :LAUFZEITBEGINN, :LAUFZEITENDE, :BEWILLIGUNGSDATUM, :BEWILLIGUNGSSUMME)"
                        cursor.execute(query, {'FKZ': row['FKZ'], 'verbundbezeichnung': row['verbundbezeichnung'], 'THEMA': row['THEMA'], 'LAUFZEITBEGINN': row['LAUFZEITBEGINN'], 'LAUFZEITENDE': row['LAUFZEITENDE'], 'BEWILLIGUNGSDATUM': row['BEWILLIGUNGSDATUM'], 'BEWILLIGUNGSSUMME': row['BEWILLIGUNGSSUMME']})
                    connection.commit()
                    
                if all(key in data[0] for key in ["FKZ", "COMPANYNAME", "FOUNDEDDATE", "URL", "EMAIL", "TEL", "STREET", "ZIPCODE", "CITY", "DESCRIPTION"]):
                    # Insert the remaining fields and fkz into another table
                    for row in data:
                        query = "INSERT INTO COMPANY (FKZ, COMPANYNAME, FOUNDEDDATE, URL, EMAIL, TEL, STREET, ZIPCODE, CITY, DESCRIPTION) VALUES (:FKZ, :COMPANYNAME, :FOUNDEDDATE, :URL, :EMAIL, :TEL, :STREET, :ZIPCODE, :CITY, :DESCRIPTION)"
                        cursor.execute(query, {'FKZ': row['FKZ'], 'COMPANYNAME': row['COMPANYNAME'], 'FOUNDEDDATE': row['FOUNDEDDATE'], 'URL': row['URL'], 'EMAIL': row['EMAIL'], 'TEL': row['TEL'], 'STREET': row['STREET'], 'ZIPCODE': row['ZIPCODE'], 'CITY': row['CITY'], 'DESCRIPTION': row['DESCRIPTION']})
                    connection.commit()
                
                return jsonify({"message": "Data uploaded successfully"}), 200
        except IntegrityError as e:
            # Handle the integrity violation (e.g., duplicate primary key)
            connection.rollback()  # Rollback the transaction
            return render_template('try_again.html', message="Integrity violation - Duplicate primary key")
        except Exception as e:
            # Handle other exceptions as needed
            connection.rollback()  # Rollback the transaction
            return jsonify({"error": str(e)}), 400
        
    return '''
        <form method="POST" action="/update-row" enctype="multipart/form-data">
            <input type="file" name="file">
            <input type="submit" value="Upload">
        </form>
    '''
@app.route("/try-again", methods=["GET"])
def try_again():
    return '''
        <form method="POST" action="/update-row" enctype="multipart/form-data">
            <input type="file" name="file">
            <input type="submit" value="Try Again">
        </form>
    '''
    
if __name__ == '__main__':
    app.run(debug=True)


"""


            if file.filename.endswith('.csv'):
                # Handle CSV file
                data = []
                stream = file.stream
                csv_data = csv.reader(stream)
                for row in csv_data:
                    data.append(row)
                
                for row in data:
                    query = "INSERT INTO projektdaten_webservice (institution, projecttitle) VALUES (:institution, :projecttitle)"
                    cursor.execute(query, {'institution': row[0], 'projecttitle': row[1]})
                connection.commit()
                return jsonify({"message": "Data uploaded successfully"}), 200

                
                
@app.route('/')
def index():
    cursor = connection.cursor()
    cursor.execute("select projecttitle, startdate from PROJEKTDATEN_WEBSERVICE where companyname = 'OMQ GmbH'")
    
    for title, date in cursor:
        print("Values:", title, date)
    cursor.close()
    connection.close()

@app.route("/input-word", methods=["GET", "POST"])
def input_word():
    if request.method == "POST":
        data = request.form.get("word")
        return jsonify({"message": f"You entered the word: {data}"}), 200

    return '''
        <form method="POST" action="/input-word">
            <label for="word">Enter a word:</label>
            <input type="text" id="word" name="word">
            <input type="submit" value="Submit">
        </form>
    '''
@app.route("/update-institution", methods=["GET", "POST"])
def create_projekt():
    if request.method == "POST":
        new_institution  = request.form.get("institution")
        query="insert into projektdaten_webservice (institution) values (:institution)"
        cursor.execute(query, {'institution': new_institution})
        connection.commit()
        return jsonify({"message": f"You entered the word: {new_institution}"}), 200

    return '''
        <form method="POST" action="/update-institution">
            <label for="word">Enter new institution name:</label>
            <input type="text" id="institution" name="institution">
            <input type="submit" value="Submit">
        </form>
    '''   
if __name__ == "__main__":
    app.run(debug=True)"""