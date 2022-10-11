from multiprocessing import connection
import sqlite3

# define connection(to connect to a database) and cursor(to interact with a database), the thing specified in brackets is the database name
connection = sqlite3.connect('314_database.db')

#create user table

command1 = """CREATE TABLE IF NOT EXISTS
User(user_id INTEGER PRIMARY KEY, login_email )"""