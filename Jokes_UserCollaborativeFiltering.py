import numpy as np
import pandas as pd
import sqlite3 as db

def weight_factor(x, y):
    # Współczynnik wagi implikuje relację między użytkownikiem x i użytkownikiem y
    t1, t2, t3 = 0, 0, 0 
    for i, j in zip(x, y):
        t1 += i * j
        t2 += i * i
        t3 += j * j
    return t1 / (np.sqrt(t2) * np.sqrt(t3))

def connect_to_database(sql_db):

    db_loc = 'data/{}.db'.format(sql_db)
    conn = db.connect(db_loc)
    c = conn.cursor()
    return conn, c

def select_normalized_ratings(conn):

    query_normalized = 'SELECT * FROM normalized_ratings'
    normalized_ratings_df = pd.read_sql(query_normalized, conn)
    return normalized_ratings_df

def select_ratings(conn):

    query_ratings = 'SELECT * FROM ratings'
    ratings_df = pd.read_sql(query_ratings, conn)
    return ratings_df

def select_complete_and_sparse_ratings(normalized_ratings_df):

    complete_ratings = normalized_ratings_df[normalized_ratings_df['number_of_jokes_rated'] == 100]
    sparse_ratings = normalized_ratings_df[normalized_ratings_df['number_of_jokes_rated'] != 100]
    return complete_ratings, sparse_ratings

def select_random_active_user(sparse_ratings):

    active_user_id = np.random.choice(sparse_ratings['user_id'], 1)[0]
    return active_user_id

def calculate_similarity(active_user_rating_list, complete_ratings):

    similarity = np.array([(complete_ratings.iloc[i, 0],\
                 weight_factor(active_user_rating_list, complete_ratings.iloc[i, 2:]))\
                 for i in range(complete_ratings.shape[0])])
    ind = np.argsort(similarity[:,1])
    similarity = similarity[ind]
    return similarity

def select_random_neighbours(similarity, num_neighbours=30):
    # Wybór losowych sąsiadów
    neighbours = similarity[similarity[:,1] > 0.1]
    index_selected_neighbours = np.random.choice(range(len(neighbours)), num_neighbours, replace=False)
    selected_neighbours = neighbours[index_selected_neighbours]
    return selected_neighbours

def select_recommendation_columns(active_user_rating):
    # Wybieramy kolumny do polecenia
    return [column for column in active_user_rating.columns if active_user_rating[column].values[0] == 0]

def calculate_active_user_mean_rating(active_user_id, ratings_df, recommendation_columns):
    # Obliczamy średnią ocenę aktywnego użytkownika
    active_user_raw_ratings = ratings_df[ratings_df['user_id'] == active_user_id].iloc[:, 2:]
    return np.mean(active_user_raw_ratings.drop(recommendation_columns, axis=1).values)

def suggest_joke(neighbours_df, neighbour_user_similarity, active_user_mean_rating):

    top_score = -np.inf
    joke_to_suggest = ''
    for column in neighbours_df.columns:
        score = score_user_item(column, neighbours_df, neighbour_user_similarity, active_user_mean_rating)
        if score > top_score:
            top_score = score
            joke_to_suggest = column
    return top_score, joke_to_suggest

def score_user_item(item_id, neighbours_df, neighbour_user_similarity, active_user_mean_rating):
    # Oblicz wynik dla danego żartu
    item_rating = neighbours_df[item_id]
    t1, t2 = 0, 0
    for similarity, norm_rating in zip(neighbour_user_similarity, item_rating):
        t1 += norm_rating * similarity
        t2 += similarity
    score = (t1 + active_user_mean_rating) / t2
    return score

def main():
    # Połącz się z bazą danych
    sql_db = 'jester_jokes'
    conn, c = connect_to_database(sql_db)

    normalized_ratings_df = select_normalized_ratings(conn)
    ratings_df = select_ratings(conn)

    complete_ratings, sparse_ratings = select_complete_and_sparse_ratings(normalized_ratings_df)

    # Wybieramy losowego aktywnego użytkownika
    active_user_id = select_random_active_user(sparse_ratings)
    print("Wybierz losowego użytkownika o ID {} jako aktywnego użytkownika, dla którego będziemy polecać żart".format(str(active_user_id)))

    # Wyświetlamy oceny danego przez aktywnego użytkownika dla 100 żartów
    active_user = sparse_ratings[sparse_ratings['user_id'] == active_user_id]
    active_user_rating = active_user.iloc[:, 2:]
    print('Oceny danego przez aktywnego użytkownika {} dla 100 żartów'.format(str(active_user_id)))
    print(active_user_rating)

    # Zapisujemy oceny aktywnego użytkownika do listy
    active_user_rating_list = active_user_rating.values.ravel()

    # Obliczamy podobieństwo między aktywnym użytkownikiem a wszystkimi sąsiadami wśród kompletnych użytkowników
    similarity = calculate_similarity(active_user_rating_list, complete_ratings)

    # Wybieramy losowych sąsiadów
    neighbours = select_random_neighbours(similarity)
    print('Mamy {} potencjalnych sąsiadów! Teraz wybierzemy losowo 30 próbek spośród nich'.format(len(neighbours)))

    # Poprzez replace=False, zapewniamy, że nie zostanie wybrany żaden sąsiad więcej niż raz
    selected_neighbours = neighbours

    # Wybieramy kolumny do polecenia
    recommendation_columns = select_recommendation_columns(active_user_rating)

    # Obliczamy średnią ocen aktywnego użytkownika
    active_user_mean_rating = calculate_active_user_mean_rating(active_user_id, ratings_df, recommendation_columns)

    # Wybieramy żart do polecenia
    neighbour_user_id = selected_neighbours[:, 0]

    # Wybieramy podobieństwo użytkowników sąsiadów
    neighbour_user_similarity = selected_neighbours[:, 1]

    # Wyświetlamy identyfikatory użytkowników sąsiadów i ich podobieństwo
    print('Identyfikatory użytkowników sąsiadów: ', neighbour_user_id, '\n\n')
    print('Podobieństwo użytkowników sąsiadów: ', neighbour_user_similarity)

    # Filtrujemy ramkę danych sąsiadów na podstawie identyfikatora użytkownika
    neighbours_df = complete_ratings[complete_ratings['user_id'].isin(neighbour_user_id)]

    print('Zaproponujemy jeden z {} żartów aktywnemu użytkownikowi \n\n'.format(len(recommendation_columns)))

    # Wybieramy tylko żarty, które nie zostały jeszcze ocenione przez aktywnego użytkownika
    neighbours_df = neighbours_df[recommendation_columns]
    print(neighbours_df.head())

    top_score, joke_to_suggest = suggest_joke(neighbours_df, neighbour_user_similarity, active_user_mean_rating)

    print('Najwyższa ocena to', top_score)
    print('Najwyższą ocenę, spośród wszystkich nieocenionych żartów, otrzymał żart', joke_to_suggest)
    
    # Wyświetlamy wybrany żart z bazy danych
    query_joke = 'SELECT * FROM jokes WHERE joke_id = ?'
    joke_data = c.execute(query_joke, (int(joke_to_suggest.split('_')[1]),)).fetchone()

    if joke_data:
        joke_id, joke_text = joke_data
        print('\nWybrany żart (numer {}):'.format(joke_id))
        print(joke_text)
    else:
        print('\nNie udało się znaleźć żartu o numerze {} w bazie danych.'.format(joke_to_suggest))


if __name__ == "__main__":
    main()
