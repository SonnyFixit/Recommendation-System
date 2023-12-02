import numpy as np
import pandas as pd
import sqlite3 as db

def connect_to_database(sql_db):
    # Połączenie się z bazą danych (lub utwórznie, jeśli nie istnieje)
    db_loc = 'data/{}.db'.format(sql_db)
    conn = db.connect(db_loc)
    c = conn.cursor()
    return conn, c

def replace_99(ratings):
    # Zamiana 99 na NaN
    joke_ids = ratings.columns[2:]    
    for joke_id in joke_ids: 
        ratings[joke_id] = ratings[joke_id].replace([99], np.nan)
    return ratings

def normalization(ratings):
    # Normalizujemy dane - odejmujemy średnią dla każdego użytkownika
    total_users = ratings.shape[0]
    for i in range(total_users):
        ratings.iloc[i, 2:] = ratings.iloc[i, 2:] - np.mean(ratings.iloc[i, 2:])
    return ratings

def replace_0(ratings):
    # Zamieniamy NaN na 0
    joke_ids = ratings.columns[2:]    
    for joke_id in joke_ids: 
        ratings[joke_id] = ratings[joke_id].replace([np.nan], 0)
    return ratings

def insert_normalized_ratings_to_database(c, normalized_ratings):

    schema = "CREATE TABLE normalized_ratings(user_id Integer, number_of_jokes_rated Integer,"
    for i in range(1, 101):
        schema = schema + 'joke_{} FLOAT(2), '.format(str(i))
    schema = schema[:-2] + ')'
    c.execute(schema)

    query =  'INSERT INTO normalized_ratings VALUES('
    for i in range(0, 102):
        query = query + '?,'
    query = query[:-1] + ')'

    # Zapisujemy znormalizowane oceny do bazy danych
    c.executemany(query, normalized_ratings.values)

def calculate_similarity(x, dataframe):
    # Obliczamy podobieństwo między użytkownikiem x a każdym innym użytkownikiem
    similarity = [weight_factor(x, dataframe.iloc[i, 2:]) for i in range(dataframe.shape[0])]
    return similarity

def weight_factor(x, y):
    # Współczynnik wagi implikuje relację między użytkownikiem x i użytkownikiem y
    # Znane również jako podobieństwo między użytkownikiem x i użytkownikiem y
    t1, t2, t3 = 0, 0, 0 
    for i, j in zip(x, y):
        t1 += i * j
        t2 += i * i
        t3 += j * j
    return t1 / (np.sqrt(t2) * np.sqrt(t3))

def main():
    # Połącz z bazą danych
    sql_db = 'jester_jokes'
    conn, c = connect_to_database(sql_db)

    # Wybierz ramkę danych z ocenami
    query = 'SELECT * FROM ratings'
    ratings_df = pd.read_sql(query, conn)
    
    # Bierzemy tylko 10 użytkowników i 8 żartów do monitorowania
    r_df = ratings_df.iloc[0:10, 0:10]

    # Zamień 99 na NaN, znormalizuj, zamień NaN na 0 i zapisz znormalizowane dane do bazy SQL
    temp1 = replace_99(r_df)
    temp2 = normalization(temp1)
    temp3 = replace_0(temp2)

    # Wybierz oceny znormalizowane dla wszystkich użytkowników
    normalized_ratings = replace_99(ratings_df)
    normalized_ratings = normalization(normalized_ratings)
    normalized_ratings = replace_0(normalized_ratings)

    # Wstaw znormalizowane oceny do bazy danych
    insert_normalized_ratings_to_database(c, normalized_ratings)

    # Zapisz zmiany w bazie danych
    conn.commit()

    # Przykład: Oblicz podobieństwo między użytkownikiem 0 a innymi użytkownikami
    active_user_ratings = temp3.iloc[0, 2:]
    similarity = calculate_similarity(active_user_ratings, temp3)
    print("Podobieństwo aktywnego użytkownika do innych użytkowników:", similarity)

if __name__ == "__main__":
    main()
