import tkinter as tk
import threading
from tkinter import PhotoImage, font as tkFont
from pathlib import Path

from Jokes_SQLInsertion import main as main_sql_insertion
from Jokes_DataPreprocessing import main as main_data_preprocessing
from Jokes_UserCollaborativeFiltering import main as main_user_collaborative_filtering

class App(tk.Tk):
    # Initialize the main application window.
    def __init__(self):
        super().__init__()
        self.title("Jokes Recommendation System")
        self.initialize_gui_elements()
        self.update_database_status()

    # Initialize the GUI elements like buttons and text area.
    def initialize_gui_elements(self):
        self.result_area = tk.Text(self, height=30, width=100)
        self.result_area.pack()

        buttonFont = tkFont.Font(family="Helvetica", size=12, weight="bold")  # Customize font

        # Initialize buttons with specified styles
        self.combined_button = tk.Button(self, text="Run SQL Insertion and Data Preprocessing", 
                                         command=self.execute_sql_insertion_and_data_preprocessing_combined, 
                                         bg="green", fg="white", font=buttonFont, padx=10, pady=5)
        self.collaborative_filtering_button = tk.Button(self, text="Run User Collaborative Filtering", 
                                                        command=self.execute_user_collaborative_filtering, 
                                                        bg="blue", fg="white", font=buttonFont, padx=10, pady=5)

        # Initially pack both buttons
        self.combined_button.pack(pady=5)
        self.collaborative_filtering_button.pack(pady=5)

    # Check the database status and update the GUI accordingly.
    def update_database_status(self):
        db_status_text, icon_path, db_exists = self.check_database()

        # Load the image and keep a reference to prevent garbage collection
        self.status_image = PhotoImage(file=icon_path)

        # Update the labels and icons based on database status
        if hasattr(self, 'db_status'):
            self.db_status.config(text=db_status_text)
            self.icon_label.config(image=self.status_image)
        else:
            self.db_status = tk.Label(self, text=db_status_text)
            self.db_status.pack()
            self.icon_label = tk.Label(self, image=self.status_image)
            self.icon_label.pack()

        # Update button visibility based on the database status
        if db_exists:
            self.collaborative_filtering_button.pack(pady=5)
            self.combined_button.pack_forget()
        else:
            self.combined_button.pack(pady=5)
            self.collaborative_filtering_button.pack_forget()

    # Check if the database file exists and return the appropriate status and icon path.
    @staticmethod
    def check_database():
        db_path = Path("Data/jester_jokes.db")
        if db_path.is_file():
            return f"Database found at: \n{db_path.absolute()}.", "Icons/Status_Okay.png", True
        else:
            return "Database not found.", "Icons/Status_Error.png", False

    # Run the user collaborative filtering process and display the result.
    def execute_user_collaborative_filtering(self):
        result = main_user_collaborative_filtering()
        self.result_area.insert(tk.END, result + "\n")

    # Start SQL insertion and data preprocessing in a separate thread.
    def execute_sql_insertion_and_data_preprocessing_combined(self):
        threading.Thread(target=self.run_db_operations, daemon=True).start()
            
    # Execute SQL insertion and data preprocessing operations.
    def run_db_operations(self):
        self.result_area.insert(tk.END, "Starting SQL Insertion...\n")
        self.result_area.update_idletasks()  # Update the GUI
        main_sql_insertion()
        self.result_area.insert(tk.END, "SQL Insertion completed.\n\n")
        self.result_area.update_idletasks()  # Update the GUI

        self.result_area.insert(tk.END, "Starting Data Preprocessing...\n")
        self.result_area.update_idletasks()  # Update the GUI
        main_data_preprocessing()
        self.result_area.insert(tk.END, "Data Preprocessing completed.\n\n")
        self.result_area.update_idletasks()  # Update the GUI

        self.update_database_status()

if __name__ == "__main__":
    app = App()
    app.mainloop()
