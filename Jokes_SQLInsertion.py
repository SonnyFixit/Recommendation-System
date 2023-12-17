import sqlite3 as db
import os
import codecs
import pandas as pd
import html2text
import numpy as np

# Connect to the database
def connect_to_database(sql_db):
    db_path = 'data/{}.db'.format(sql_db)
    conn = db.connect(db_path)
    return conn

# Create a 'cursor' to execute commands
# For each user, only these 5 tables will be created, in which all data will be collected.
def create_tables(cursor):
    cursor.execute("CREATE TABLE IF NOT EXISTS jokes (joke_id INTEGER, joke TEXT)")
    
    schema = "CREATE TABLE IF NOT EXISTS ratings(user_id Integer, number_of_jokes_rated Integer,"
    for i in range(1, 101):
        schema += 'joke_{} FLOAT(2), '.format(i)
    schema = schema[:-2] + ')'
    cursor.execute(schema)
    
# Extract the joke from the HTML file
def extract_joke_from_html(file):
    with codecs.open(file, 'r', encoding="cp1252") as data:
        joke_html = data.read()
    joke = html2text.html2text(joke_html)
    joke_id = int(file.split('init')[1].split('.html')[0])
    return joke_id, joke

#Saving jokes into database
def insert_jokes_to_database(cursor):
    files = os.listdir('data/raw/jokes')
    jokes_list = [extract_joke_from_html('data/raw/jokes/' + file) for file in files if file.endswith('.html')]
    cursor.executemany('INSERT INTO jokes VALUES (?,?)', jokes_list)

# Saving ratings to database
def insert_ratings_to_database(cursor, dataframe):
    query = 'INSERT INTO ratings VALUES(' + ','.join(['?' for _ in dataframe.columns]) + ')'
    cursor.executemany(query, dataframe.values)

 # Reading data from Excel files
def read_rating_data():
    df1 = pd.read_excel('data/raw/jester-data-1.xls', header=None)
    df2 = pd.read_excel('data/raw/jester-data-2.xls', header=None)
    df3 = pd.read_excel('data/raw/jester-data-3.xls', header=None)
    return pd.concat([df1, df2, df3], axis=0)

def main():
    
    conn = connect_to_database('jester_jokes')
    # Create a 'cursor' to execute commands
    c = conn.cursor()

    create_tables(c)
    insert_jokes_to_database(c)
    dataframe = read_rating_data()
    
    user_id = np.linspace(1, len(dataframe), len(dataframe))
    dataframe.insert(0, 'user_id', user_id)
    
    insert_ratings_to_database(c, dataframe)
    conn.commit()

    query = 'SELECT * FROM ratings'
    df = pd.read_sql(query, conn)
    print(df.tail())
    df.to_csv('data/jester_jokes_rating.csv', index=None)

    conn.close()

if __name__ == "__main__":
    main()
