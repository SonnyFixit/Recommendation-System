import numpy as np
import pandas as pd
import sqlite3 as db

# Connect to the database (or create it, in case it doesn't exist)
def connect_to_database(sql_db):
    db_loc = 'data/{}.db'.format(sql_db)
    conn = db.connect(db_loc)
    c = conn.cursor()
    return conn, c

# Replace 99 with NaN
def replace_99(ratings):
    joke_ids = ratings.columns[2:]    
    for joke_id in joke_ids: 
        ratings[joke_id] = ratings[joke_id].replace([99], np.nan)
    return ratings

# Normalize the data - subtract the mean for each user
def normalization(ratings):
    total_users = ratings.shape[0]
    for i in range(total_users):
        ratings.iloc[i, 2:] = ratings.iloc[i, 2:] - np.mean(ratings.iloc[i, 2:])
    return ratings

# Replace NaN with 0
def replace_0(ratings):
    joke_ids = ratings.columns[2:]    
    for joke_id in joke_ids: 
        ratings[joke_id] = ratings[joke_id].replace([np.nan], 0)
    return ratings

# Store normalized ratings in the database
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

    c.executemany(query, normalized_ratings.values)

# Calculate similarity between user x and each other user
def calculate_similarity(x, dataframe):
    similarity = [weight_factor(x, dataframe.iloc[i, 2:]) for i in range(dataframe.shape[0])]
    return similarity

# The weight factor implies the relationship between user x and user y
# Also known as the similarity between user x and user y
def weight_factor(x, y):
    t1, t2, t3 = 0, 0, 0 
    for i, j in zip(x, y):
        t1 += i * j
        t2 += i * i
        t3 += j * j
    return t1 / (np.sqrt(t2) * np.sqrt(t3))

def main():
    
    # Connect to the database
    sql_db = 'jester_jokes'
    conn, c = connect_to_database(sql_db)

    # Select the dataframe with ratings
    query = 'SELECT * FROM ratings'
    ratings_df = pd.read_sql(query, conn)
    
    # Take only 10 users and 8 jokes for monitoring
    r_df = ratings_df.iloc[0:10, 0:10]

    # Replace 99 with NaN, normalize, replace NaN with 0 and save the normalized data to SQL
    temp1 = replace_99(r_df)
    temp2 = normalization(temp1)
    temp3 = replace_0(temp2)

    # Select normalized ratings for all users
    normalized_ratings = replace_99(ratings_df)
    normalized_ratings = normalization(normalized_ratings)
    normalized_ratings = replace_0(normalized_ratings)

    # Insert normalized ratings into the database
    insert_normalized_ratings_to_database(c, normalized_ratings)

    # Save changes to the database
    conn.commit()

    # Example: Calculate the similarity between user 0 and other users
    active_user_ratings = temp3.iloc[0, 2:]
    similarity = calculate_similarity(active_user_ratings, temp3)
    print("Similarity of the active user to other users:", similarity)

if __name__ == "__main__":
    main()
