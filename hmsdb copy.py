import tkinter as tk
from tkinter import messagebox
#from PIL import Image, ImageTk
import mysql.connector

# insert names for each - provided na ng system dapat, mamimili nalang yung patient
doctors = {
    "Dra. Dalusung": ["9:00 AM - 10:00 AM", "2:00 PM - 3:00 PM"],
    "Dra. Festejo": ["10:00 AM - 11:00 AM", "3:00 PM - 4:00 PM"],
    "Dra. Isip": ["7:00 AM - 8:00 AM", "5:00 - 6:00 PM"],
    "Dr. Sutare": ["11:00 AM - 12:00 PM", "7:00 - 8:00 PM"],
}

# dictionary to store appointments
appointments = {}

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="hms_db"
)

# Create a cursor for executing SQL queries
cursor = mydb.cursor()

# Function to insert a new patient into the database during signup
def insert_patient_into_db(username, password):
    try:
        query = "INSERT INTO patients (username, password) VALUES (%s, %s)"
        cursor.execute(query, (username, password))
        mydb.commit()
        return True
    except Exception as e:
        print("Error while inserting into the database:", str(e))
        mydb.rollback()
        return False

# Function to validate login credentials against the database


def check_login_credentials(username, password):
    query = "SELECT * FROM patients WHERE username = % AND password = %"
    cursor.execute(query, (username, password))
    result = cursor.fetchone()
    return result is not None

def create_login_box():
    global username_entry, password_entry
    login_box = tk.Frame(root, borderwidth=2, relief="ridge", padx=10, pady=10)
    login_box.pack(padx=20, pady=20)

    username_label = tk.Label(login_box, text="E-mail Address:") #baguhin dapat yung nasa database, Username to E-mail
    username_label.pack(anchor="w")
    username_entry = tk.Entry(login_box)
    username_entry.pack(fill="x", padx=10, pady=5)

    password_label = tk.Label(login_box, text="Password:")
    password_label.pack(anchor="w")
    password_entry = tk.Entry(login_box, show="*")
    password_entry.pack(fill="x", padx=10, pady=5)

    login_button = tk.Button(login_box, text="Login", command=login)
    login_button.pack(pady=10)


def create_signup_box():
    global First_name_entry, Last_name_entry, email_entry, password_entry
    signup_box = tk.Frame(root, borderwidth=2, relief="ridge", padx=10, pady=10)
    signup_box.pack(padx=20, pady=20)

    Username_label = tk.Label(signup_box, text="Username:")
    Username_label.pack(anchor="w")
    Username_entry = tk.Entry(signup_box)
    Username_entry.pack(fill="x", padx=10, pady=5)

    email_label = tk.Label(signup_box, text="Email Address:")
    email_label.pack(anchor="w")
    email_entry = tk.Entry(signup_box)
    email_entry.pack(fill="x", padx=10, pady=5)

    password_label = tk.Label(signup_box, text="Password:")
    password_label.pack(anchor="w")
    password_entry = tk.Entry(signup_box, show="*")
    password_entry.pack(fill="x", padx=10, pady=5)

    create_acc_button = tk.Button(signup_box, text="Create Account", command=signup)
    create_acc_button.pack(pady=10)


def login():
    global username_entry, password_entry
    username = username_entry.get()
    password = password_entry.get()
    if username and password:
        if check_login_credentials(username, password):
            open_appointment_window()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")
    else:
        messagebox.showerror("Invalid Information", "Please fill in both username and password.")

login_window = None

def open_appointment_window():
    login_window.destroy()

    appointment_window = tk.Tk()
    appointment_window.title("Appointment Scheduling")

    def schedule_appointment():
        patient_name = name_entry.get()
        age = age_entry.get()
        contact_number = contact_entry.get()
        sex = sex_var.get()
        selected_doctor = doctor_var.get()
        selected_slot = slot_var.get()
        appointment_datetime = date_time_entry.get()

        appointment_info = {
            "Name": patient_name,
            "Age": age,
            "Contact Number": contact_number,
            "Sex": sex,
            "Doctor": selected_doctor,
            "Slot": selected_slot,
            "Appointment Date and Time": appointment_datetime,
        }

        if patient_name and age and contact_number and appointment_datetime:
            appointments[patient_name] = appointment_info
            messagebox.showinfo("Appointment Scheduled", "Appointment scheduled successfully!")
        else:
            messagebox.showerror("Invalid Information", "Please fill in all required fields.")

    name_label = tk.Label(appointment_window, text="Name:")
    name_label.pack()
    name_entry = tk.Entry(appointment_window)
    name_entry.pack()

    age_label = tk.Label(appointment_window, text="Age:")
    age_label.pack()
    age_entry = tk.Entry(appointment_window)
    age_entry.pack()

    contact_label = tk.Label(appointment_window, text="Contact Number:")
    contact_label.pack()
    contact_entry = tk.Entry(appointment_window)
    contact_entry.pack()

    sex_label = tk.Label(appointment_window, text="Sex:")
    sex_label.pack()
    sex_var = tk.StringVar()
    sex_var.set("Male")
    sex_radio_male = tk.Radiobutton(appointment_window, text="Male", variable=sex_var, value="Male")
    sex_radio_female = tk.Radiobutton(appointment_window, text="Female", variable=sex_var, value="Female")
    sex_radio_male.pack()
    sex_radio_female.pack()

    doctor_label = tk.Label(appointment_window, text="Select Doctor:")
    doctor_label.pack()
    doctor_var = tk.StringVar()
    doctor_var.set("Dra. Dalusung")  
    doctor_var.set("Dra. Festejo")  
    doctor_var.set("Dra. Isip")  
    doctor_var.set("Dr. Sutare")  
    doctor_option_menu = tk.OptionMenu(appointment_window, doctor_var, *doctors.keys())
    doctor_option_menu.pack()

    slot_label = tk.Label(appointment_window, text="Select Slot:")
    slot_label.pack()
    slot_var = tk.StringVar()
    slot_var.set(doctors[doctor_var.get()][0])  # default slot based on selected doctor
    slot_option_menu = tk.OptionMenu(appointment_window, slot_var, *doctors[doctor_var.get()])
    slot_option_menu.pack()

    date_time_label = tk.Label(appointment_window, text="Appointment Date and Time (e.g., 2023-01-01 10:00 AM):")
    date_time_label.pack()
    date_time_entry = tk.Entry(appointment_window)
    date_time_entry.pack()

    schedule_button = tk.Button(appointment_window, text="Schedule Appointment", command=schedule_appointment)
    schedule_button.pack()

    appointment_window.mainloop()

def signup():
    global username_entry, email_entry, password_entry
    username = email_entry.get()
    password = password_entry.get()
    if username and password:
        if insert_patient_into_db(username, password):
            messagebox.showinfo("Signup Successful", "Account created successfully!")
        else:
            messagebox.showerror("Signup Failed", "Failed to create an account. Please try again.")
    else:
        messagebox.showerror("Invalid Information", "Please fill in all the informations needed.")

# Create the main window
root = tk.Tk()
root.geometry("700x500")
root.title("Hospital Management System")

# Load and display the background image
#background_image = Image.open("E:\Final Project\super final\download.jpg")
#background_image = background_image.resize((700, 500), Image.Resampling.NEAREST)
#background_photo = ImageTk.PhotoImage(background_image)

#background_label = tk.Label(root, image=background_photo)
#background_label.place(x=0, y=0, relwidth=1, relheight=1)


label = tk.Label(root,
                 text="Hospital Management System",
                 font=("Times", "24", "bold"),
                 fg="red"
                 )
label.pack(padx=50, pady=10)

label = tk.Label(root,
                 text="REGISTRATION FORM:",
                 font=("Times", "14"),
                 fg="black"
                 )
label.pack(padx=50, pady=10)

create_signup_box()

# button to switch to the login page - code copy from chloie once done
login_page_button = tk.Button(root, text="Already have an account? Log in here.", command=create_login_box)
login_page_button.pack()

# initialize login_box frame but hide it
login_box = tk.Frame(root, borderwidth=2, relief="ridge", padx=10, pady=10)
login_box.pack()
login_box.place_forget()  # Hide the login form initially

root.mainloop()