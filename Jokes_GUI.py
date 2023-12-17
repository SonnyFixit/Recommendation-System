import tkinter as tk

from Jokes_SQLInsertion import main as main_sql_insertion
from Jokes_DataPreprocessing import main as main_data_preprocessing
from Jokes_UserCollaborativeFiltering import main as main_user_collaborative_filtering
from pathlib import Path
from tkinter import PhotoImage

def check_database():
    db_path = Path("Data/jester_jokes.db")
    if db_path.is_file():
        return "Database found.", "Icons/Status_Okay.png", True
    else:
        return "Database not found.", "Icons/Status_Error.png", False

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Jokes Recommendation System")

        db_status_text, icon_path, db_exists = check_database()
        self.db_status = tk.Label(self, text=db_status_text)
        self.db_status.pack()

        self.status_icon = PhotoImage(file=icon_path)
        self.icon_label = tk.Label(self, image=self.status_icon)
        self.icon_label.pack()

        self.result_area = tk.Text(self, height=30, width=100)
        self.result_area.pack()

        if db_exists:
            tk.Button(self, text="Run User Collaborative Filtering", command=self.execute_user_collaborative_filtering).pack()
        else:
            tk.Button(self, text="Run SQL Insertion and Data Preprocessing", command=self.execute_sql_insertion_and_data_preprocessing_combined).pack()

    def execute_user_collaborative_filtering(self):

        result = main_user_collaborative_filtering()
        self.result_area.insert(tk.END, result + "\n")

    def execute_sql_insertion_and_data_preprocessing_combined(self):

            sql_insertion_result = main_sql_insertion()
            self.result_area.insert(tk.END, sql_insertion_result + "\n")


            data_preprocessing_result = main_data_preprocessing()
            self.result_area.insert(tk.END, data_preprocessing_result + "\n")

if __name__ == "__main__":
    app = App()
    app.mainloop()
