from multiprocessing import connection
import sqlite3
import hashlib

from sqlite3 import Error
connection =''
cursorObj = ''

def sql_connection():
    try:
        # define connection(to connect to a database) and cursor(to interact with a database), the thing specified in brackets is the database name
        connection = sqlite3.connect('db.sqlite3')
        return connection

    except Error:
        print(Error)

def sql_table(connection):
        cursorObj = connection.cursor()
        return cursorObj
def hash_string(string):
    return hashlib.sha224(string.encode('utf-8')).hexdigest()
#add to main_user
#0 - system admin
#1 - conference chair
#2 - reviewer
#3 - author
connection = sql_connection()
cursorObj = sql_table(connection)
cursorObj.execute("INSERT INTO main_user VALUES (001, 'ashleylogan19@gmail.com',"+ hash_string('19ash204yolo') + ", 'Ashley Logan',false, 0, 0)")
cursorObj.execute("INSERT INTO main_user VALUES (002, 'jenniferhaul33@gmail.com', "+ hash_string('jen2haul005') + ", 'Jennifer Haul', false, 0, 0)")
cursorObj.execute("INSERT INTO main_user VALUES (003, 'pranovsidhvik@gmail.com',"+ hash_string('sid@pranic292') + ", 'Pranov Sidhvik', false, 0, 0)")
cursorObj.execute("INSERT INTO main_user VALUES (004, 'chanyouman3teng@gmail.com',"+ hash_string('chan82$nasafol') + ", 'Chan You Man Teng', false, 0, 0)")

