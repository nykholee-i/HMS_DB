import tkinter as tk
from tkinter import messagebox
#from PIL import Image, ImageTk
import mysql.connector

mydb = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="",
    database="hms_db"
)

# Create a cursor for executing SQL queries
cursor = mydb.cursor()

# Function to insert a new user into the database during signup
def insert_users_into_db(username, email, password):
    try:
        query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, email, password))
        mydb.commit()
        return True
    except Exception as e:
        print("Error while inserting into the database:", str(e))
        mydb.rollback()
        return False

# Function to validate login credentials against the database

def check_login_credentials(email, password):
    query = "SELECT * FROM users WHERE email = %s AND password = %s"
    cursor.execute(query, (email, password))
    result = cursor.fetchone()
    return result is not None

login_window = None

def create_login_box():
    global email_entry, password_entry, login_window, signup_box  # Make signup_box global
    login_box = tk.Frame(root, borderwidth=2, relief="ridge", padx=10, pady=10)
    login_box.pack(padx=20, pady=20)

    email_label = tk.Label(login_box, text="Email Address:")
    email_label.pack(anchor="w")
    email_entry = tk.Entry(login_box)
    email_entry.pack(fill="x", padx=10, pady=5)

    password_label = tk.Label(login_box, text="Password:")
    password_label.pack(anchor="w")
    password_entry = tk.Entry(login_box, show="*")
    password_entry.pack(fill="x", padx=10, pady=5)

    login_button = tk.Button(login_box, text="Login", command=login)
    login_button.pack(pady=10)

    # Hide the signup_box if it exists
    if signup_box:
        signup_box.pack_forget()

    # Initialize the signup_box as None
    signup_box = None

def create_signup_box():
    global username_entry, email_entry, password_entry, signup_box
    signup_box = tk.Frame(root, borderwidth=2, relief="ridge", padx=10, pady=10)
    signup_box.pack(padx=20, pady=20)

    username_label = tk.Label(signup_box, text="Username:")
    username_label.pack(anchor="w")
    username_entry = tk.Entry(signup_box)
    username_entry.pack(fill="x", padx=10, pady=5)

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
    global email_entry, password_entry
    email = email_entry.get()
    password = password_entry.get()
    if email and password:
        if check_login_credentials(email, password):
            appointment_window()
        else:
            messagebox.showerror("Login Failed", "Invalid email or password")
    else:
        messagebox.showerror("Invalid Information", "Please fill in both email and password.")

def signup():
    global username_entry, email_entry, password_entry
    username = username_entry.get()
    email = email_entry.get()
    password = password_entry.get()
    if username and email and password:
        if insert_users_into_db(username, email, password):
            messagebox.showinfo("Signup Successful", "Account created successfully!")
        else:
            messagebox.showerror("Signup Failed", "Failed to create an account. Please try again.")
    else:
        messagebox.showerror("Invalid Information", "Please fill in all the informations needed.")

def appointment_window():
    # Create an appointment frame within the main window
    appointment_window = tk.Toplevel(root)
    appointment_window.title("Appointment Scheduling")
    
    # Create an appointment frame within the appointment window
    appointment_frame = tk.Frame(appointment_window, borderwidth=2, relief="ridge", padx=10, pady=10)
    appointment_frame.pack(padx=20, pady=20)

    # Hide the main window
    root.withdraw()

    def hide_login_box():
        login_box.place_forget()

    hide_login_box()

    def schedule_appointment():
        patient_name = name_entry.get()
        age = age_entry.get()
        contact_number = contact_entry.get()
        sex = sex_var.get()
        selected_doctor = doctor_var.get()
        selected_slot = slot_var.get()
        appointment_date = date_entry.get()
        selected_reason = reasons_var.get()  # Get the selected reason

        if patient_name and age and contact_number and appointment_date:
            # Calculate the amount based on the selected reason
            if selected_reason == "Checkup":
                amount = "500 pesos"
            elif selected_reason == "Medication":
                amount = "1,200 pesos"
            else:
                amount = "Unknown"

            appointment_info = {
                "Name": patient_name,
                "Age": age,
                "Contact Number": contact_number,
                "Sex": sex,
                "Doctor": selected_doctor,
                "Appointment Date": appointment_date,
                "Reason": selected_reason,  # Add selected reason
                "Amount to be Paid": amount  # Add amount
        }
            appointments[patient_name] = appointment_info
            messagebox.showinfo("Appointment Scheduled", "Appointment scheduled successfully!")

            ##### show appointment summary after successful appointment scheduling
            show_appointment_summary(appointment_info)

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

    reasons_label = tk.Label(appointment_window, text="Reason of Appointment:")
    reasons_label.pack()
    reasons_var = tk.StringVar()
    reasons_var.set("Checkup")
    reasons_radio_checkup = tk.Radiobutton(appointment_window, text="Checkup", variable=reasons_var, value="Checkup")
    reasons_radio_medication = tk.Radiobutton(appointment_window, text="Medication", variable=reasons_var, value="Medication")
    reasons_radio_checkup.pack()
    reasons_radio_medication.pack()

    # Create a dictionary to store doctors and their available slots
    doctors = {
        "Dra. Dalusung": ["9:00 AM - 10:00 AM", "2:00 PM - 3:00 PM"],
        "Dra. Festejo": ["10:00 AM - 11:00 AM", "3:00 PM - 4:00 PM"],
        "Dra. Isip": ["7:00 AM - 8:00 AM", "5:00 PM - 6:00 PM"],
        "Dr. Sutare": ["11:00 AM - 12:00 PM", "7:00 PM - 8:00 PM"],
        }

    # Dictionary to store appointments
    appointments = {}

    doctor_label = tk.Label(appointment_window, text="Select Doctor:")
    doctor_label.pack()
    doctor_var = tk.StringVar(value=list(doctors.keys())[0])  # Set the default doctor
    doctor_option_menu = tk.OptionMenu(appointment_window, doctor_var, *doctors.keys())
    doctor_option_menu.pack()

    def update_slot_options(*args):
        selected_doctor = doctor_var.get()
        # Update the slots when the doctor changes
        slot_option_menu['menu'].delete(0, 'end')  # Clear the current slots
        for slot in doctors[selected_doctor]:
            slot_option_menu['menu'].add_command(label=slot, command=tk._setit(slot_var, slot))

    doctor_var.trace("w", update_slot_options)  # Update slots when the doctor changes

    slot_label = tk.Label(appointment_window, text="Select Slot:")
    slot_label.pack()
    slot_var = tk.StringVar(value=doctors[doctor_var.get()][0])  # Set the default slot
    slot_option_menu = tk.OptionMenu(appointment_window, slot_var, *doctors[doctor_var.get()])
    slot_option_menu.pack()

    date_label = tk.Label(appointment_window, text="Appointment Date (e.g., 2023-01-01):")
    date_label.pack()
    date_entry = tk.Entry(appointment_window)
    date_entry.pack()

    schedule_button = tk.Button(appointment_window, text="Schedule Appointment", command=schedule_appointment)
    schedule_button.pack()

    # Create a button to go back to the main window
    back_button = tk.Button(appointment_frame, text="Back to Main", command=show_main_window)
    back_button.pack()
   
    # Make sure to destroy the appointment frame properly when it's closed
    appointment_frame.protocol("WM_DELETE_WINDOW", show_main_window)

    appointment_window.mainloop()

#### Appointment Summary
def show_appointment_summary(appointment_info):
    summary_window = tk.Toplevel(root)
    summary_window.title("Appointment Summary")

    for key, value in appointment_info.items():
        label = tk.Label(summary_window, text=f"{key}: {value}")
        label.pack()

    summary_window.mainloop()

    ##############################################################################################
    root.withdraw()

    def hide_appointment_window():
        appointment_window.place_forget()

    hide_appointment_window()
#################################################################################################

def show_main_window():
    # Show the main window again
    root.deiconify()

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

# button to switch to the login page
login_page_button = tk.Button(root, text="Already have an account? Log in here.", command=create_login_box)
login_page_button.pack()

# initialize login_box frame but hide it
login_box = tk.Frame(root, borderwidth=2, relief="ridge", padx=10, pady=10)
login_box.pack()
login_box.place_forget()  # Hide the login form initially

root.mainloop()