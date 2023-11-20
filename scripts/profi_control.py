# -*- coding: utf-8 -*-

# 26.07.2021
# Python 3.8
# Windows 10

import binascii
import cx_Oracle
import pandas as pd
import re
from datetime import datetime
from bs4 import BeautifulSoup
import os
import urllib
from dateutil.relativedelta import relativedelta
import json

import logging_to_file as log
from ora_int_credentials import OraIntCredentials
from stdArgParser import getStandardArgParser


class ProfiControl:

    def __init__(self, user, password, storeInKeyring=False, setDefaultUser=False):
        serviceId = 'TIVIANINTERFACE_ORACLE'
        defaultUserKey = 'DEFAULT_USERNAME'
        if storeInKeyring or user is None or password is None: import keyring
        if storeInKeyring:
            if user is None: raise ValueError('OracleControl:  Cannot store password when no username is given!')
            if password is None: raise ValueError('OracleControl: Cannot store password when no password is given!')
            keyring.set_password(serviceId, user, password)
            if setDefaultUser:
                keyring.set_password(serviceId, defaultUserKey, user)
        self.username = user if user is not None else keyring.get_password(serviceId, defaultUserKey)
        self.password = password if password is not None else keyring.get_password(serviceId, self.username)
        oracreds = OraIntCredentials(self.username, self.password)

        try:  # in case Ora Client lib has already been initialized
            cx_Oracle.init_oracle_client(lib_dir=oracreds.clientDirectory())
        except Exception:
            pass
        self.dsn_tns = cx_Oracle.makedsn(oracreds.url(),
                                         oracreds.port(),
                                         service_name=oracreds.serviceName())
        self.connect()
        self.participantsInDB = dict()

    def connect(self):
        '''Builds connection to Oracle Server'''
        try:
            self.con = cx_Oracle.connect(self.username,
                                         self.password,
                                         self.dsn_tns)
            self.cursor = self.con.cursor()
        except Exception:
            # in ora_int_credentials.py checken, ob der richtige Pfad zum instaclient einkommentiert ist
            log.logging.error('Cannot connect to Oracle database.')
            exit()

    def getFPsByCondition(self, vars, table, condition=None, condition_vars=None, distinct=False):
        try:
            '''Finds the given variables in given Oracle table
            or View that match a given condition.

            Args:
                vars: A list or dict containing the variables to select
                    from the given table.
                table: A string containing the Oracle table
                    from which to get the data.
                condition: A string containing an sql condition.
                    (incl. "WHERE").
                condition_vars: A list or dict containing the vars for the condition 

            Returns:
                data_dicts: A list containing dicts
                    (one per Foerderprojekt)
                    which contain the data found in the table
            '''
            if distinct:
                sql_query = "SELECT DISTINCT {} FROM {} {}".format(', '.join(vars), table, condition)
            else:
                sql_query = "SELECT {} FROM {} {}".format(', '.join(vars), table, condition)
            # print(sql_query)
            try:
                if condition_vars is None:
                    self.cursor.execute(sql_query)
                else:
                    self.cursor.execute(sql_query, condition_vars)
                self.con.commit()
            except Exception as ex:
                raise Exception('Could not execute sql query "{}": {}'.format(sql_query, ex))
            fps = self.cursor.fetchall()  # list
            fps_dicts = []
            # falls eine Spalte aus dem oracle-view ein clob ist (pconatcts), muss
            # es extra ausgelesen werden, bei allen anderen reicht =
            columns = [d[0] for d in self.cursor.description]
            fps_dicts = [{var: f.read() if type(f) == cx_Oracle.LOB else f for var, f in zip(columns, fp)} for fp in
                         fps]
            return fps_dicts
        except Exception as e:
            log.logging.error('{}->{}: {}'.format(os.path.basename(__file__), 'getFPsByCondition()', e))
            raise

    def setSurveyQuestions(self, questions_dict, commit=True):
        '''Inserts the Questions of a given Questback
        survey into the Oracle Questions table.

        Args:
            questions_dict: A dictionary containing all
                the information about the questions of a survey
                in the form of: {surveyId: {qId: (qText, qType),
                qId: (qText, qType) ... }}
        '''
        success = True
        for survey_id, questions in questions_dict.items():
            for qId, qInfo in questions.items():  # qInfo ist (qText, qType)
                qText_html = qInfo[0]
                # get rid of html tags used in the survey
                soup = BeautifulSoup(qText_html, features="html.parser")
                qText = soup.get_text()
                qText = qText.replace(u'\xa0', u' ')
                qType = qInfo[1]
                sql_cmd = 'MERGE INTO EFS_QUESTIONS USING dual \
                            ON ( SURVEYID=:survey_id and QID=:qId) \
                            WHEN MATCHED THEN \
                                UPDATE SET QTEXT=:qText, QTYPE=:qType\
                            WHEN NOT MATCHED THEN \
                                INSERT (SURVEYID, QID, QTEXT, QTYPE) \
                                VALUES (:survey_id, :qId, :qText, :qType)'
                try:
                    self.cursor.execute(sql_cmd, dict(survey_id=survey_id, qId=qId, qText=qText, qType=qType))
                    if commit: self.con.commit()
                except cx_Oracle.IntegrityError:
                    success = False
                    continue
                except Exception as e:
                    log.logging.error(f"An error occured while "
                                      f"trying to insert questions "
                                      f"into table 'EFS_QUESTIONS'. "
                                      f"\n SQL command: {sql_cmd} "
                                      f"\n Error message: {e}")
        if success is False:
            log.logging.warning(f"Some or all questions from survey "
                                f"{survey_id} already exist "
                                f"in table 'EFS_QUESTIONS'.")

    def setQuestionValues(self, survey_id, values_dict, commit=True):
        for question in values_dict:
            q_id = question['varname']
            if 'categories' in question:
                # meaning there are several vordefinierte Ausprägungen
                # to choose from
                poss_values_html = str(question['categories'])
                # get rid of html tags used in the survey
                soup = BeautifulSoup(poss_values_html, features="html.parser")
                poss_values = soup.get_text()
                poss_values = poss_values.replace(u'\xa0', u' ')
                poss_values = poss_values.replace("'", '"')
                sql_cmd = 'MERGE INTO EFS_QUESTIONS USING dual \
                            ON ( SURVEYID=:survey_id and QID=:qId) \
                            WHEN MATCHED THEN \
                                UPDATE SET QVALUES=:poss_values\
                            WHEN NOT MATCHED THEN \
                                INSERT (SURVEYID, QID,QVALUES) \
                                VALUES (:survey_id, :qId, :poss_values)'
                self.cursor.execute(sql_cmd, dict(poss_values=poss_values, survey_id=survey_id, qId=q_id))
                if commit: self.con.commit()
            else:
                pass

    def executeSQL(self, strSQL, vars, commit=True):
        try:
            if vars is None:
                self.cursor.execute(strSQL)
            else:
                self.cursor.execute(strSQL, vars)
            if commit: self.con.commit()
        except Exception as e:
            log.logging.error("An error occured while executing query {}. Error message: {}".format(strSQL, e))
            raise

    def getScalarResult(self, strSQL, vars):
        '''
        Return single value 
        
        Args:
            strSQL: valid SQL String
        '''

        try:
            if vars is None:
                self.cursor.execute(strSQL)
            else:
                self.cursor.execute(strSQL, vars)

            return self.cursor.fetchone()[0]
        except Exception as e:
            log.logging.error("An error getting scalar result. Query: {}. Error message: {}".format(strSQL, e))
            return None

    def getResultTable(self, strSQL, vars):
        '''
        Return resultset from sql query
        
        Args:
            strSQL: valid SQL String
        '''

        try:
            if vars is None:
                self.cursor.execute(strSQL)
            else:
                self.cursor.execute(strSQL, vars)
            fps = self.cursor.fetchall()

            return fps
        except Exception as e:
            log.logging.error("An error getting result table. Query: {}. Error message: {}".format(strSQL, e))
            return None

    def getParticipantList(self, surveyId):
        participants = self.getResultTable('select fkz, email, personid from efs_participants where surveyid=:id',
                                           [surveyId])
        self.participantsInDB.update({surveyId: participants})

    def tryConvertInt(self, i, onError=None):
        try:
            return int(i)
        except:
            return onError

    #moved from set_foerderprojekte
    def getMailingDates(self, startDate, endDate, rules):
        datelist = [self.getSingleMailingDate(startDate, endDate, rule) for rule in rules]
        if len([d for d in datelist if d is not None]) == 0: return [datetime.now().date()]
        return datelist

    #moved from set_foerderprojekte
    def updateProjects(self, qbcon, view, surveyRules, tivianProjects, oracleProjects):
        print('Updating projects')
        ok = 0
        skipped = 0
        failed = 0
        j = 0
        filteredRules = [rfilt for rfilt in surveyRules if rfilt['SURVEY_ID'] in view['surveys']]
        hasNoRules = [v for v in view['surveys'] if len([r for r in filteredRules if v == r['SURVEY_ID']]) == 0]
        allPersonTypes = None if len(filteredRules) == 0 or len(hasNoRules) > 0 \
            else {t for r in filteredRules for t in json.loads(r['PERSONTYPES'], strict=False)}
        for fp in oracleProjects:
            j += 1
            print('\rUploading/updating project "{}" ({}/{})'.format( \
                fp['FKZ'], j, len(oracleProjects)), end='', flush=True)
            try:
                startDate = datetime.strptime(fp['Projektstart'], '%Y-%m-%d').date()
            except Exception as ex:
                startDate = None
            try:
                endDate = datetime.strptime(fp['Projektende'], '%Y-%m-%d').date()
            except Exception as ex:
                endDate = None
            try:
                updated = qbcon.set_foerderprojekt(fp, allPersonTypes, tivianProjects.get(fp['FKZ']))
                for surveyId, survey in view['surveys'].items():
                    filteredRules = [rfilt for rfilt in surveyRules if rfilt['SURVEY_ID'] == surveyId]
                    personTypes = [None] if len(filteredRules) == 0 else {t for r in filteredRules for t in
                                                                        json.loads(r['PERSONTYPES'], strict=False)}
                    mailingDates = self.getMailingDates(startDate, endDate, filteredRules)
                    maxMailingDate = max(mailingDates)
                    minMailingDate = min(mailingDates)
                    
                    if survey['LOGPARTICIPANTS'] == 1:
                        allowInsert = datetime.now().date() <= maxMailingDate + relativedelta(days=1)
                        for personType in personTypes:
                            qbcon.update_efs_participants(self, surveyId, view['PTARGET'], fp['FKZ'],
                                                    personType, fp['Projektbeteiligte'], minMailingDate, allowInsert)
                if updated:
                    ok += 1
                else:
                    skipped += 1
            except Exception as e:
                print(' Failed!')
                log.logging.error('set_foerderprojekte: could not update project {}: {}'.format(fp['FKZ'], e))
                print('set_foerderprojekte: could not update project {}: {}'.format(fp['FKZ'], e))
                failed += 1
        if failed == 0:
            print(' OK')
        else:
            print()
            print('upload failed for {} of {} projects'.format(failed, len(oracleProjects)))
        return (ok, skipped, failed)

    def getAllDataSql(self, person_id):
        """
        Retrieves all data for a given person ID from the SQL database.

        Args:
            person_id (int): The person ID.

        Returns:
            dict: A dictionary containing the retrieved data.
        """
        #spalte name weg lassen von str
        sql = """
        select 
        'FKZ: ' || pd.fkz ,'AKRONYM: ' ||  pm.akronym, 'Laufzeit: ' || gd.laufzeitbeginn || ' bis ' || gd.laufzeitende,
        'BW: ' || pd.admptemail bw, 'WTM: ' || pd.fachptemail wtm, 
        'PERSONID: ' || cp.personid, 'FORENAME: ' || cp.forename,'SURNAME: ' ||  cp.surename
        from 
        (((I_profi_personendaten pd inner join projectpersons pp on pd.fkz = pp.fkz)
        inner join contactperson cp on pp.personid = cp.personid)
        inner join projectmetadata pm on pd.fkz=pm.fkz)
        inner join i_profi_grunddaten gd on pd.v_nr = gd.v_nr
        where 
        cp.personid = {}
        """.format(person_id)

        result_table = self.getResultTable(sql, None)
        
        if result_table:
            column_names = [desc[0].lower() for desc in self.cursor.description]
            result_list = [dict(zip(column_names, row)) for row in result_table]
            
            # Process the result list as needed
            for result_row in result_list:
                # Access individual fields using result_row['column_name']
                return(result_row)
        else:
            return("No data found from getAllDataSql.")

    def getTsguidList(self):
        # Fetch the TSGUIDs from the system_log table
        sql = "SELECT TSGUID FROM system_log WHERE statuscode = 400 and status = 0"
        result_table = self.getResultTable(sql, None)
        
        if result_table:
            return [binascii.hexlify(row[0]).decode('utf-8') for row in result_table]
        else:
            return []

    def fetchRowData(self, tsguid):
        # Convert the TSGUID back to bytes
        tsguid_bytes = binascii.unhexlify(tsguid)

        # Fetch row data for the given TSGUID
        sql = """
        SELECT TS, ORIGIN, MSG
        FROM system_log
        WHERE TSGUID = :tsguid
        """
        result_table = self.getResultTable(sql, [tsguid_bytes])
        
        if result_table:
            column_names = [desc[0].lower() for desc in self.cursor.description]
            result_row = dict(zip(column_names, result_table[0]))
            return result_row
        else:
            return {}        
        
    def updateStatusInSystemLog(self):
        sql = "UPDATE system_log SET status = 1 WHERE (statuscode = 200 and status = 0) or (statuscode = 100 and status = 0)"
        self.executeSQL(sql, None)
    
    def getTitleFromSurveyid(self, surveyid):
        title = self.getScalarResult("select title from efs_surveys where survey_id = {}".format(surveyid), None)
        return title