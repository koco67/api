from flask import flash, jsonify
import logging_to_file as log
import os
import win32com.client as win32
import profi_control



class Status:
    INCORRECT_LOGIN = 401 #Can be caused by missing, invalid or expired token or username/password combination.
    NO_FILE = 401
    No_FILE_SELECTED = 401
    
    @staticmethod
    def setStatus(code, *args):

        if code == 401: 
            if(args[0]=="INCORRECT_LOGIN"):
                flash("Username or password is incorrect", 'error')
            elif(args[0]=="NO_FILE"):
                return jsonify({"error": "No file found to upload"}), 400
            elif(args[0]=="NO_FILE_SELECTED"):
                flash("No file selected, please select a csv or json file", 'error')
    
        else:
            return jsonify({"error": "Unknown status code"}), 400