import os
import pandas as pd
import sqlite3
from natsort import natsorted 

def create_table(connection):
    cursor = connection.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS jokes (file_name TEXT, content TEXT)')
    connection.commit()

def insert_into_database(connection, file_name, content):
    cursor = connection.cursor()
    cursor.execute('INSERT INTO jokes (file_name, content) VALUES (?, ?)', (file_name, content))
    connection.commit()

def process_folder(folder_path, connection):
    create_table(connection)


    for file_name in natsorted(os.listdir(folder_path)):
        file_path = os.path.join(folder_path, file_name)

        if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
            print(f"Processing Excel file: {file_name}")
            extract_text_from_excel(file_path, connection)
            print("    Entries inserted into the database.")

def extract_text_from_excel(file_path, connection):
    try:

        df = pd.read_excel(file_path, engine='openpyxl', header=None)


        for i, text in enumerate(df.iloc[:, 0], 1):
            insert_into_database(connection, f"Text {i}", text)

    except Exception as e:
        print(f"An error occurred while processing Excel file: {e}")

if __name__ == "__main__":
    folder_path = input("Enter the path to the folder containing Excel files: ")

    if not os.path.exists(folder_path):
        print(f"The specified folder '{folder_path}' does not exist.")
    else:
        db_name = input("Enter the name for the SQLite database (without extension): ")
        db_name_with_extension = db_name + '.db'
        connection = sqlite3.connect(db_name_with_extension)

        process_folder(folder_path, connection)

        connection.close()

        print(f"Entries saved to SQLite database: {db_name_with_extension}")
