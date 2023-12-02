import sqlite3 as db
import re
import os
import codecs
import pandas as pd
import html2text
import numpy as np

# Połącz z bazą danych (lub utwórz, jeśli nie istnieje)
sql_db = 'jester_jokes'
db_path = 'data/{}.db'.format(sql_db)
conn = db.connect(db_path)

# Utwórz 'kursor' do wykonywania poleceń
c = conn.cursor()

# Dla każdego użytkownika utworzone zostaną tylko te 5 tabele, w których będą zbierane wszystkie dane.
c.execute("CREATE TABLE IF NOT EXISTS jokes (joke_id INTEGER, joke TEXT)")

schema = "CREATE TABLE IF NOT EXISTS ratings(user_id Integer, number_of_jokes_rated Integer,"
for i in range(1, 101):
    schema = schema + 'joke_{} FLOAT(2), '.format(str(i))
schema = schema[:-2] + ')'
c.execute(schema)

file = 'init1.html'
data = codecs.open('data/raw/jokes/' + file, 'r', encoding="cp1252")
joke_html = data.read()

# Wydobcie żartu z pliku HTML
joke = html2text.html2text(joke_html)
# Wyodrębnienie identyfikatora żartu
joke_id = int(file.split('init')[1].split('.html')[0])

print(joke_id)
print(joke)

# Metoda przyjmuje lokalizację pliku HTML jako wejście i zwraca z tego żart
def joke_extractor(file):
    data = codecs.open(file, 'r', encoding="cp1252")
    joke_html = data.read()
    joke = html2text.html2text(joke_html)
    joke_id = int(file.split('init')[1].split('.html')[0])
    return (joke_id, joke)

files = os.listdir('data/raw/jokes')
jokes_list = [joke_extractor('data/raw/jokes/'+ file) for file in files if file.endswith('.html')]

c.executemany('INSERT INTO jokes VALUES (?,?)', jokes_list)

conn.commit()

def insert_ratings_to_database(c, dataframe):

    query = 'INSERT INTO ratings VALUES(' + ','.join(['?' for _ in range(len(dataframe.columns))]) + ')'
    c.executemany(query, dataframe.values)

def main():
    
    # odczytywanie danych  z plików excel
    df1 = pd.read_excel('data/raw/jester-data-1.xls', header=None)
    df2 = pd.read_excel('data/raw/jester-data-2.xls', header=None)
    df3 = pd.read_excel('data/raw/jester-data-3.xls', header=None)
    
    dataframe = pd.concat([df1, df2, df3], axis=0)
    
    user_id = np.linspace(1, len(dataframe), len(dataframe))
    dataframe.insert(0, 'user_id', user_id)

    # Zapisanie ocen do bazy danych
    insert_ratings_to_database(c, dataframe)
    
    # Zapisanie zmian w bazie danych
    conn.commit()

    # Wyświetl ostatnie kilka wierszy tabeli 'ratings'(w ramach sprawdzenia)
    query = 'SELECT * FROM ratings'
    df = pd.read_sql(query, conn)
    print(df.tail())

    # Zapisaie danych do pliku CSV (na wszelki wypadek)
    df.to_csv('data/jester_jokes_rating.csv', index=None)

if __name__ == "__main__":
    main()
