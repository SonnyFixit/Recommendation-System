import os
import pandas as pd
import sqlite3
from bs4 import BeautifulSoup
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

    # Use natsorted to sort files naturally
    for file_name in natsorted(os.listdir(folder_path)):
        file_path = os.path.join(folder_path, file_name)

        if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
            print(f"Processing Excel file: {file_name}")
            extract_text_from_excel(file_path, connection)
            print("    Entries inserted into the database.")

        elif file_name.endswith('.html'):
            print(f"Processing HTML file: {file_name}")
            extract_text_from_html(file_path, connection)
            print("    Entry inserted into the database.")

def extract_text_from_excel(file_path, connection):
    try:
        # Load the Excel file into a DataFrame without considering the first row as a header
        df = pd.read_excel(file_path, engine='openpyxl', header=None)

        # Insert into the database
        for i, text in enumerate(df.iloc[:, 0], 1):
            insert_into_database(connection, f"Text {i}", text)

    except Exception as e:
        print(f"An error occurred while processing Excel file: {e}")

def extract_text_from_html(file_path, connection):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
            soup = BeautifulSoup(html_content, 'html.parser')
            body_tag = soup.body
            content_to_save = body_tag.get_text(separator='\n', strip=True) if body_tag else "No body content found."

            # Extract the file number from the file name
            file_number = int(''.join(filter(str.isdigit, os.path.splitext(file_path)[0])))

            insert_into_database(connection, f"Text {file_number}", content_to_save)

    except Exception as e:
        print(f"An error occurred while processing HTML file: {e}")

if __name__ == "__main__":

    folder_path = input("Enter the path to the folder containing Excel and HTML files: ")


    if not os.path.exists(folder_path):
        print(f"The specified folder '{folder_path}' does not exist.")
    else:
        db_name = input("Enter the name for the SQLite database (without extension): ")
        db_name_with_extension = db_name + '.db'
        connection = sqlite3.connect(db_name_with_extension)

        process_folder(folder_path, connection)

        connection.close()

        print(f"Entries saved to SQLite database: {db_name_with_extension}")
