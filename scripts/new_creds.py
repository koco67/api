import api_methods
from profi_control import ProfiControl
from stdArgParser import getStandardArgParser
import api_methods

parser = getStandardArgParser()
args = parser.parse_args()
cursor1 = ProfiControl(args.oracleUser, args.oraclePassword, args.saveCredentials, args.setDefaultUser)


def store_credentials(username, password):
    print("1")
    # Hash the password before storing it in the database
    hashed_password = api_methods.hash_password(password)

    # Store the username and hashed password in the Oracle table
    query = "INSERT INTO API_USERS (username, password_hash) VALUES (:username, :password_hash)"
    cursor1.executeSQL(query, {'username': username, 'password_hash': hashed_password})
    print("done")


store_credentials("new","a")