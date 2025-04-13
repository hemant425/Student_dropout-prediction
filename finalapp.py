import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3, os, pickle
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt

model = pickle.load(open(r"C:\Users\heman\OneDrive\Documents\Python projects\Mini project-5 sem\Jarvis\student_dropout\dropout_model.pkl", "rb"))

class DropoutApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Dropout Prediction System")
        self.root.attributes('-fullscreen', True)

        self.bg_color = "#f0f4f7"
        self.header_color = "#2e8b57"
        self.button_color = "#4CAF50"
        self.entry_bg = "#ffffff"
        self.text_font = ("Segoe UI", 12)

        self.root.configure(bg=self.bg_color)
        self.create_db()
        self.show_login_register_screen()

        # Bind fullscreen toggle
        self.root.bind("<F11>", lambda e: self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen")))
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))

    def create_db(self):
        conn = sqlite3.connect("studentdata.db")
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            roll TEXT UNIQUE,
            password TEXT
        )''')
        conn.commit()
        conn.close()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def add_header(self, parent, title):
        header = tk.Label(parent, text=title, font=("Segoe UI", 24, "bold"), bg=self.header_color, fg="white", pady=10)

        header.pack(fill='x')

    def styled_button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, font=self.text_font, bg=self.button_color, fg="white", padx=10, pady=5, relief="raised", bd=2, activebackground="#388e3c")

    def show_login_register_screen(self):
        self.clear_window()
        self.add_header(self.root, "Student Dropout Prediction")
        frame = tk.Frame(self.root, bg=self.bg_color, padx=20, pady=20)
        frame.pack(expand=True)

        

        tk.Label(frame, text="Welcome to the Prediction System", font=("Segoe UI", 16), bg=self.bg_color).pack(pady=20)
        self.styled_button(frame, "Login", self.show_login_form).pack(pady=10)
        self.styled_button(frame, "Register", self.show_register_form).pack(pady=10)
        self.styled_button(frame, "Exit", self.root.quit).pack(pady=10)

    def show_register_form(self):
        self.clear_window()
        frame = tk.Frame(self.root, bg=self.bg_color, padx=20, pady=20)
        frame.pack(expand=True)

        self.add_header(self.root, "Register")

        entries = {}
        fields = ["Full Name", "Roll No", "Password"]
        for i, field in enumerate(fields):
            tk.Label(frame, text=field + ":", font=self.text_font, bg=self.bg_color).grid(row=i, column=0, pady=10, sticky='e')
            entry = tk.Entry(frame, show="*" if "Password" in field else "", font=self.text_font, bg=self.entry_bg)
            entry.grid(row=i, column=1, pady=10, padx=10)
            entries[field] = entry

        def register():
            name, roll, pwd = entries["Full Name"].get(), entries["Roll No"].get(), entries["Password"].get()
            if not (name and roll and pwd):
                messagebox.showerror("Error", "All fields are required.")
                return
            try:
                with sqlite3.connect("studentdata.db") as conn:
                    conn.execute("INSERT INTO students (name, roll, password) VALUES (?, ?, ?)", (name, roll, pwd))
                messagebox.showinfo("Success", "Registered successfully!")
                self.show_login_register_screen()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Roll No already exists.")

        self.styled_button(frame, "Submit", register).grid(column=0, row=4, columnspan=2, pady=10)
        self.styled_button(frame, "Back", self.show_login_register_screen).grid(column=0, row=5, columnspan=2)

    def show_login_form(self):
        self.clear_window()
        self.add_header(self.root, "Login")
        frame = tk.Frame(self.root, bg=self.bg_color, padx=20, pady=20)
        frame.pack(expand=True)

        

        tk.Label(frame, text="Roll No:", font=self.text_font, bg=self.bg_color).grid(row=0, column=0, pady=10)
        roll_entry = tk.Entry(frame, font=self.text_font, bg=self.entry_bg)
        roll_entry.grid(row=0, column=1, pady=10)

        tk.Label(frame, text="Password:", font=self.text_font, bg=self.bg_color).grid(row=1, column=0, pady=10)
        password_entry = tk.Entry(frame, show="*", font=self.text_font, bg=self.entry_bg)
        password_entry.grid(row=1, column=1, pady=10)

        def login():
            roll, pwd = roll_entry.get(), password_entry.get()
            with sqlite3.connect("studentdata.db") as conn:
                cur = conn.cursor()
                cur.execute("SELECT name FROM students WHERE roll=? AND password=?", (roll, pwd))
                data = cur.fetchone()
                if data:
                    self.current_user = roll
                    self.student_name = data[0]
                    self.ensure_log_folder()
                    self.show_subject_input()
                else:
                    messagebox.showerror("Error", "Invalid credentials.")

        self.styled_button(frame, "Login", login).grid(column=0, row=3, columnspan=2, pady=10)
        self.styled_button(frame, "Back", self.show_login_register_screen).grid(column=0, row=4, columnspan=2)

    def show_subject_input(self):
        self.clear_window()
        self.add_header(self.root, f"Welcome, {self.student_name}")
        frame = tk.Frame(self.root, bg=self.bg_color, padx=20, pady=20)
        frame.pack()

        

        tk.Label(frame, text="Enter number of subjects (1 to 10):", font=self.text_font, bg=self.bg_color).pack(pady=10)
        self.subject_count_entry = tk.Entry(frame, font=self.text_font, bg=self.entry_bg)
        self.subject_count_entry.pack(pady=5)

        self.styled_button(frame, "Next", self.create_subject_inputs).pack(pady=10)
        self.styled_button(frame, "View History", self.view_logs).pack(pady=5)
        self.styled_button(frame, "Graph Analysis", self.plot_graph).pack(pady=5)
        self.styled_button(frame, "Logout", self.show_login_register_screen).pack(pady=10)

    def create_subject_inputs(self):
        try:
            count = int(self.subject_count_entry.get())
            if count < 1 or count > 10:
                raise ValueError
        except:
            messagebox.showerror("Error", "Enter valid subject count (1-10).")
            return

        self.subject_entries = []
        self.clear_window()
        self.add_header(self.root, "Enter Marks for CIE1 to CIE5")

        form_frame = tk.Frame(self.root, bg=self.bg_color)
        form_frame.pack()

        for i in range(count):
            for j in range(5):
                label = f"Subject {i+1} - CIE{j+1}:"
                tk.Label(form_frame, text=label, font=self.text_font, bg=self.bg_color).grid(row=i*5+j, column=0, pady=5)
                entry = tk.Entry(form_frame, font=self.text_font, bg=self.entry_bg)
                entry.grid(row=i*5+j, column=1, pady=5)
                self.subject_entries.append(entry)

        self.styled_button(self.root, "Predict", self.predict).pack(pady=20)
        self.styled_button(self.root, "Back", self.show_subject_input).pack()

    def predict(self):
        try:
            self.user_marks = [float(e.get()) for e in self.subject_entries]
            if not all(0 <= mark <= 100 for mark in self.user_marks):
                raise ValueError
        except:
            messagebox.showerror("Error", "Please enter valid marks (0-100).")
            return

        while len(self.user_marks) < 55:
            self.user_marks.append(0.0)

        total_subjects = len(self.user_marks) // 5
        subject_averages = [sum(self.user_marks[i*5:i*5+5])/5 for i in range(total_subjects)]
        overall_avg = sum(subject_averages) / total_subjects

        self.result = "Likely to Dropout" if overall_avg < 40 else "Safe"
        self.log_prediction()
        self.show_result()

    def show_result(self):
        self.clear_window()
        self.add_header(self.root, "Prediction Result")

        color = "red" if self.result == "Likely to Dropout" else "green"
        tk.Label(self.root, text=f"You are: {self.result}", font=("Segoe UI", 16, "bold"), fg=color, bg=self.bg_color).pack(pady=20)
        self.styled_button(self.root, "Download PDF", self.generate_pdf).pack(pady=10)
        self.styled_button(self.root, "Back to Home", self.show_subject_input).pack(pady=10)

    def ensure_log_folder(self):
        os.makedirs("user_data/logs", exist_ok=True)

    def log_prediction(self):
        log_file = f"user_data/logs/{self.current_user}.txt"
        with open(log_file, "a") as f:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{now} | Marks: {self.user_marks} | Result: {self.result}\n")

    def view_logs(self):
        log_file = f"user_data/logs/{self.current_user}.txt"
        if not os.path.exists(log_file):
            messagebox.showinfo("History", "No predictions yet.")
            return
        win = tk.Toplevel(self.root)
        win.title("Prediction History")
        win.geometry("600x400")
        text = tk.Text(win, font=self.text_font, bg="#fdfdfd")
        text.pack(expand=True, fill='both')
        with open(log_file, "r") as f:
            text.insert("1.0", f.read())

    def plot_graph(self):
        log_file = f"user_data/logs/{self.current_user}.txt"
        if not os.path.exists(log_file):
            messagebox.showinfo("Graph", "No data available.")
            return
        safe = dropout = 0
        with open(log_file, "r") as f:
            for line in f:
                if "Safe" in line:
                    safe += 1
                else:
                    dropout += 1
        labels = ['Safe', 'Likely to Dropout']
        sizes = [safe, dropout]
        plt.figure(figsize=(5, 5))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=["#7dd87d", "#f77c7c"])
        plt.title(f"Prediction Distribution for {self.student_name}")
        plt.axis('equal')
        plt.show()

    def generate_pdf(self):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=14)
        pdf.cell(200, 10, txt="Dropout Prediction Report", ln=True, align='C')
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Name: {self.student_name}", ln=True)
        pdf.cell(200, 10, txt=f"Roll No: {self.current_user}", ln=True)
        for i, mark in enumerate(self.user_marks[:55]):
            pdf.cell(200, 10, txt=f"Mark {i+1}: {mark}", ln=True)
        pdf.ln(5)
        pdf.cell(200, 10, txt=f"Prediction: {self.result}", ln=True)
        filename = f"{self.current_user}_dropout_report.pdf"
        pdf.output(filename)
        messagebox.showinfo("PDF Generated", f"Saved as '{filename}'")


# Run
if __name__ == "__main__":
    root = tk.Tk()
    DropoutApp(root)
    root.mainloop()
