import numpy as np
import pandas as pd
import sqlite3 as db

# The weight factor implies the relationship between user x and user y
def weight_factor(x, y):
    
    t1, t2, t3 = 0, 0, 0 
    for i, j in zip(x, y):
        t1 += i * j
        t2 += i * i
        t3 += j * j
    return t1 / (np.sqrt(t2) * np.sqrt(t3))

# Connect to the specified SQLite database
def connect_to_database(sql_db):
    
    db_loc = 'data/{}.db'.format(sql_db)
    conn = db.connect(db_loc)
    c = conn.cursor()
    return conn, c

# Retrieve normalized ratings from the database
def select_normalized_ratings(conn):

    query_normalized = 'SELECT * FROM normalized_ratings'
    normalized_ratings_df = pd.read_sql(query_normalized, conn)
    return normalized_ratings_df

# Retrieve user ratings from the database
def select_ratings(conn):

    query_ratings = 'SELECT * FROM ratings'
    ratings_df = pd.read_sql(query_ratings, conn)
    return ratings_df

# Separate ratings into 'complete' and 'sparse' based on the number of jokes rated
def select_complete_and_sparse_ratings(normalized_ratings_df):

    complete_ratings = normalized_ratings_df[normalized_ratings_df['number_of_jokes_rated'] == 100]
    sparse_ratings = normalized_ratings_df[normalized_ratings_df['number_of_jokes_rated'] != 100]
    return complete_ratings, sparse_ratings

# Randomly select an active user from the sparse ratings
def select_random_active_user(sparse_ratings):

    active_user_id = np.random.choice(sparse_ratings['user_id'], 1)[0]
    return active_user_id

# Calculate similarity between the active user and all neighbors in complete users
def calculate_similarity(active_user_rating_list, complete_ratings):

    similarity = np.array([(complete_ratings.iloc[i, 0],\
                 weight_factor(active_user_rating_list, complete_ratings.iloc[i, 2:]))\
                 for i in range(complete_ratings.shape[0])])
    ind = np.argsort(similarity[:,1])
    similarity = similarity[ind]
    return similarity

# Select random neighbors based on similarity
def select_random_neighbours(similarity, num_neighbours=30):

    neighbours = similarity[similarity[:,1] > 0.1]
    index_selected_neighbours = np.random.choice(range(len(neighbours)), num_neighbours, replace=False)
    selected_neighbours = neighbours[index_selected_neighbours]
    return selected_neighbours

# Choose columns (jokes) to recommend
def select_recommendation_columns(active_user_rating):

    return [column for column in active_user_rating.columns if active_user_rating[column].values[0] == 0]

# Calculate the mean rating of the active user
def calculate_active_user_mean_rating(active_user_id, ratings_df, recommendation_columns):

    active_user_raw_ratings = ratings_df[ratings_df['user_id'] == active_user_id].iloc[:, 2:]
    return np.mean(active_user_raw_ratings.drop(recommendation_columns, axis=1).values)

# Suggest a joke to the active user based on neighbor ratings and similarity
def suggest_joke(neighbours_df, neighbour_user_similarity, active_user_mean_rating):

    top_score = -np.inf
    joke_to_suggest = ''
    for column in neighbours_df.columns:
        score = score_user_item(column, neighbours_df, neighbour_user_similarity, active_user_mean_rating)
        if score > top_score:
            top_score = score
            joke_to_suggest = column
    return top_score, joke_to_suggest

# Calculate the score for a given joke
def score_user_item(item_id, neighbours_df, neighbour_user_similarity, active_user_mean_rating):

    item_rating = neighbours_df[item_id]
    t1, t2 = 0, 0
    for similarity, norm_rating in zip(neighbour_user_similarity, item_rating):
        t1 += norm_rating * similarity
        t2 += similarity
    score = (t1 + active_user_mean_rating) / t2
    return score

# Connect to the database
def main():

    sql_db = 'jester_jokes'
    conn, c = connect_to_database(sql_db)

    normalized_ratings_df = select_normalized_ratings(conn)
    ratings_df = select_ratings(conn)

    complete_ratings, sparse_ratings = select_complete_and_sparse_ratings(normalized_ratings_df)
    
    output = ""

    # Select a random active user
    active_user_id = select_random_active_user(sparse_ratings)
    output += "Randomly selected user ID {} as the active user for whom we will recommend a joke\n".format(str(active_user_id))
    print("Randomly selected user ID {} as the active user for whom we will recommend a joke".format(str(active_user_id)))

    # Display the ratings given by the active user for 100 jokes
    active_user = sparse_ratings[sparse_ratings['user_id'] == active_user_id]
    active_user_rating = active_user.iloc[:, 2:]
    print('Ratings given by the active user {} for 100 jokes'.format(str(active_user_id)))
    print(active_user_rating)
    output += 'Ratings given by the active user {} for 100 jokes\n'.format(str(active_user_id))
    output += str(active_user_rating) + "\n"

    # Save the active user's ratings to a list
    active_user_rating_list = active_user_rating.values.ravel()

    # Calculate the similarity between the active user and all neighbors among complete users
    similarity = calculate_similarity(active_user_rating_list, complete_ratings)

    # Select random neighbors
    neighbours = select_random_neighbours(similarity)
    print('We have {} potential neighbors! Now we will randomly select 30 samples among them'.format(len(neighbours)))
    output += 'We have {} potential neighbors! Now we will randomly select 30 samples among them\n'.format(len(neighbours))

    # Ensure that no neighbor is selected more than once with replace=False
    selected_neighbours = neighbours

    # Choose columns for recommendation
    recommendation_columns = select_recommendation_columns(active_user_rating)

    # Calculate the mean rating of the active user
    active_user_mean_rating = calculate_active_user_mean_rating(active_user_id, ratings_df, recommendation_columns)

    # Choose a joke to recommend
    neighbour_user_id = selected_neighbours[:, 0]

    # Select the similarity of neighbor users
    neighbour_user_similarity = selected_neighbours[:, 1]

    # Display the IDs of neighbor users and their similarity
    print('Neighbor user IDs: ', neighbour_user_id, '\n\n')
    print('Neighbor user similarity: ', neighbour_user_similarity)
    output += 'Neighbor user IDs: {}\n\n'.format(neighbour_user_id)
    output += 'Neighbor user similarity: {}\n\n'.format(neighbour_user_similarity)

    # Filter the neighbor dataframe based on user ID
    neighbours_df = complete_ratings[complete_ratings['user_id'].isin(neighbour_user_id)]

    print('We will propose one of {} jokes to the active user \n\n'.format(len(recommendation_columns)))
    output += 'We will propose one of {} jokes to the active user\n\n'.format(len(recommendation_columns))

    # Select only the jokes that have not yet been rated by the active user
    neighbours_df = neighbours_df[recommendation_columns]
    print(neighbours_df.head())
    output += str(neighbours_df.head()) + "\n"

    top_score, joke_to_suggest = suggest_joke(neighbours_df, neighbour_user_similarity, active_user_mean_rating)

    print('Highest score is', top_score)
    print('The highest score, among all unrated jokes, was received by the joke', joke_to_suggest)
    output += 'Highest score is {}\n'.format(top_score)
    output += 'The highest score, among all unrated jokes, was received by the joke {}\n'.format(joke_to_suggest)
    
    # Display the selected joke from the database
    query_joke = 'SELECT * FROM jokes WHERE joke_id = ?'
    joke_data = c.execute(query_joke, (int(joke_to_suggest.split('_')[1]),)).fetchone()

    if joke_data:
        joke_id, joke_text = joke_data
        print('\nSelected joke (number {}):'.format(joke_id))
        print(joke_text)
        output += '\nSelected joke (number {}):\n{}'.format(joke_id, joke_text)
    else:
        print('\nFailed to find joke number {} in the database.'.format(joke_to_suggest))
        output += '\nFailed to find joke number {} in the database.'.format(joke_to_suggest)
        
    return output


if __name__ == "__main__":
    main()
