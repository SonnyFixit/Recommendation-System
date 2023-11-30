import os
from bs4 import BeautifulSoup

def read_and_save_to_database(connection, folder_path):
    create_table(connection)

    for file_name in os.listdir(folder_path):
        if file_name.endswith('.html'):
            file_path = os.path.join(folder_path, file_name)

            if os.path.isfile(file_path):
                with open(file_path, 'r', encoding='utf-8') as file:
                    html_content = file.read()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    body_tag = soup.body
                    content_to_save = body_tag.get_text(separator='\n', strip=True) if body_tag else "No body content found."

                    insert_into_database(connection, file_name, content_to_save)

def create_table(connection):
    cursor = connection.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS jokes (file_name TEXT, content TEXT)')
    connection.commit()

def insert_into_database(connection, file_name, content):
    cursor = connection.cursor()
    cursor.execute('INSERT INTO jokes (file_name, content) VALUES (?, ?)', (file_name, content))
    connection.commit()
