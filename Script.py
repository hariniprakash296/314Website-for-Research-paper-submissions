from multiprocessing import connection
import sqlite3

# define connection(to connect to a database) and cursor(to interact with a database), the thing specified in brackets is the database name
connection = sqlite3.connect('314_database.db')

cursor = connection.cursor()

# create user table

command1 = """CREATE TABLE IF NOT EXISTS
User(user_id INTEGER PRIMARY KEY, login_email TEXT, login_pw TEXT, name TEXT, user_type TEXT)"""

cursor.execute(command1)

# create purchases table

command2 = """CREATE TABLE IF NOT EXISTS
Paper( paper_id INTEGER PRIMARY KEY, array_authors_id INTEGER, paper_name TEXT, paper_details TEXT, array_reviewer_ids INTEGER, reviewer_bid REAL, acceptance_state INTEGER,FOREIGN KEY(array_reviewer_ids) REFERENCES User(user_id), FOREIGN KEY(array_authors_id) REFERENCES User(user_id))"""

cursor.execute(command2)

# create review table

command3 = """CREATE TABLE IF NOT EXISTS
Review(review_id INTEGER, paper_id INTEGER, reviewer_id INTEGER, review_details TEXT, reviewer_rating INTEGER, author_rating INTEGER, array_comments TEXT, FOREIGN KEY(paper_id) REFERENCES Paper(Paper_id), FOREIGN KEY(reviewer_id) REFERENCES User(user_id))"""

cursor.execute(command3)

# create reviewer table

command4 = """CREATE TABLE IF NOT EXISTS
Reviewer(user_id INTEGER, max_papers INTEGER, FOREIGN KEY(user_id) REFERENCES User(user_id))"""

cursor.execute(command4)

#add to User

cursor.execute("INSERT INTO User VALUES (001, 'ashleylogan19@gmail.com', '19ash204yolo', 'Ashley Logan', 'Author')")
cursor.execute("INSERT INTO User VALUES (002, 'jenniferhaul33@gmail.com', 'jen2haul005', 'Jennifer Haul', 'Conference Chair')")
cursor.execute("INSERT INTO User VALUES (003, 'pranovsidhvik@gmail.com', 'sid@pranic292', 'Pranov Sidhvik', 'Reviewer')")
cursor.execute("INSERT INTO User VALUES (004, 'chanyouman3teng@gmail.com', 'chan82$nasafol', 'Chan You Man Teng', 'System Admin')")

#add to Paper
