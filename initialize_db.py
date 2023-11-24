import sqlite3

conn = sqlite3.connect('database.db')

cursor = conn.cursor()

create_question_table = '''
CREATE TABLE Question (
    id INTEGER PRIMARY KEY,
    title TEXT,
    body TEXT,
    votes INTEGER,
    views INTEGER,
    created_date DATETIME,
    modified_date DATETIME
);
'''

create_answer_table = '''
CREATE TABLE Answer (
    id INTEGER PRIMARY KEY,
    body TEXT,
    votes INTEGER,
    created_date DATETIME,
    question_id INTEGER,
    FOREIGN KEY (question_id) REFERENCES Question(id)
);
'''

create_tag_table = '''
CREATE TABLE Tag (
    id INTEGER PRIMARY KEY,
    name TEXT
);
'''

create_question_tag_table = '''
CREATE TABLE Question_Tag (
    question_id INTEGER,
    tag_id INTEGER,
    PRIMARY KEY (question_id, tag_id),
    FOREIGN KEY (question_id) REFERENCES Question(id),
    FOREIGN KEY (tag_id) REFERENCES Tag(id)
);
'''

cursor.execute(create_question_table)
cursor.execute(create_answer_table)
cursor.execute(create_tag_table)
cursor.execute(create_question_tag_table)

conn.commit()
conn.close()

print("SQLite database 'database.db' with tables created successfully.")
