
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






from datetime import datetime

"""
def is_valid_date(date_string, date_format="%d.%m.%y"):
    try:
        # Attempt to parse the date using the specified format
        datetime.strptime(date_string, date_format)
        return True
    except ValueError:
        return False
    
def check_dates(data):
    date_fields = ['LAUFZEITBEGINN', 'LAUFZEITENDE', 'BEWILLIGUNGSDATUM', 'FOUNDEDDATE']
    invalid_dates = []

    for field in date_fields:
        date_value = data.get(field, '')
        if not is_valid_date(date_value):
            invalid_dates.append(field)

    if invalid_dates:
        message = f"Invalid dates in fields: {', '.join(invalid_dates)}"
        # flash this message for api and return error
    else:
        return True
"""
def is_valid_date(date_string, date_format="%d.%m.%y"):
    try:
        # Attempt to parse the date using the specified format
        datetime.strptime(date_string, date_format)
        return True
    except ValueError:
        return False
    
json_data = [
        {
            "VERBUNDBEZEICHNUNG": "AAAVERBUNDBEZEICHNUNG1",
            "THEMA": "thema1",
            "LAUFZEITBEGINN": "1.12.99"
        }]
if is_valid_date(json_data[0]['LAUFZEITBEGINN']):
    print("ok")
else:
    print("not ok")