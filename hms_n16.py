import tkinter as tk
from tkinter import messagebox, scrolledtext
from PIL import Image, ImageTk
import mysql.connector
from tkinter import ttk, filedialog  # for tree
from reportlab.lib.pagesizes import letter  # for pdf
from reportlab.pdfgen import canvas  # for pdf
from tkcalendar import Calendar
from datetime import datetime
from fpdf import FPDF
from collections import defaultdict
import re  # for pdf data or doctor limits

# Maximum appointments per doctor's slot
MAX_APPOINTMENTS_PER_SLOT = 5

# Declare global variables
search_date_entry = None
search_time_var = None
search_doctor_var = None
date_entry = None

# Add these global variables at the beginning of your code
name_var = None
date_var = None
time_var = None
search_date_entry = None
patient_name = None
age = None
contact_number = None
sex = None
selected_reason = None
disease = None
selected_doctor = None
appointment_time = None
appointment_date = None
amount = None


doctor_appointments = {}  # Dictionary to store doctor appointments and their counts

bg_color = "#E0E0E0"  # Light gray
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
def insert_users_into_db(full_name, age, sex, email, password):
    try:
        query = "INSERT INTO users (full_name, age, sex, email, password) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (full_name, age, sex, email, password))
        mydb.commit()
        return True
    except Exception as e:
        print("Error while inserting into the database:", str(e))
        mydb.rollback()
        return False

def insert_admins_into_db(email, password):
    try:
        query = "INSERT INTO admins (email, password) VALUES (%s, %s)"
        cursor.execute(query, (email, password))
        mydb.commit()
        return True
    except Exception as e:
        print("Error while inserting admin credentials:", str(e))
        mydb.rollback()
        return False

# Function to validate login credentials against the database

def check_login_credentials(email, password):
    query = "SELECT * FROM users WHERE email = %s AND password = %s"
    cursor.execute(query, (email, password))
    result = cursor.fetchone()
    return result is not None

def check_admin_login_credentials(email, password):
    try:
        query = "SELECT * FROM admins WHERE email = %s AND password = %s"
        cursor.execute(query, (email, password))
        result = cursor.fetchone()
        if result:
            return True
        else:
            print("Admin login failed: Invalid email or password")
            return False
    except Exception as e:
        print("Error while checking admin login credentials:", str(e))
        return False


def get_appointments_for_doctor(doctor_id):
    try:
        query = "SELECT id, doctor, appointment_time, appointment_date FROM appointments WHERE doctor_id = %s"
        cursor.execute(query, (doctor_id,))
        appointments = cursor.fetchall()
        return appointments
    except Exception as e:
        print("Error while retrieving doctor appointments:", str(e))
        return None


def initialize_doctor_appointments():
    global doctor_appointments
    doctor_appointments = defaultdict(dict)

    try:
        query = "SELECT id, doctor, appointment_time, appointment_date FROM appointments"
        cursor.execute(query)
        appointments = cursor.fetchall()

        for appointment in appointments:
            appointment_id = appointment[0]
            doctor = appointment[1]
            slot = appointment[2]
            date = appointment[3]

            if date not in doctor_appointments[doctor]:
                doctor_appointments[doctor][date] = {slot: (1, appointment_id)}
            elif slot not in doctor_appointments[doctor][date]:
                doctor_appointments[doctor][date][slot] = (1, appointment_id)
            else:
                count, _ = doctor_appointments[doctor][date][slot]
                doctor_appointments[doctor][date][slot] = (count + 1, appointment_id)
    except Exception as e:
        print("Error while initializing doctor_appointments:", str(e))

# Call the function to initialize doctor_appointments at the beginning of the program
initialize_doctor_appointments()


def save_appointment_to_database(appointment_info):
    try:
        # Reformat the appointment date to match the expected format ("%Y-%m-%d")
        appointment_date = datetime.strptime(appointment_info["Appointment Date"], "%Y-%m-%d")
        formatted_appointment_date = appointment_date.strftime("%Y-%m-%d")

        query_existing = "SELECT COUNT(*) FROM appointments WHERE doctor = %s AND appointment_time = %s AND appointment_date = %s"
        cursor.execute(query_existing, (appointment_info["Doctor"], appointment_info["Appointment Time"], formatted_appointment_date))
        existing_count = cursor.fetchone()[0]

        if existing_count >= MAX_APPOINTMENTS_PER_SLOT:
            print("Doctor has reached the appointment limit for this slot and date.")
            messagebox.showerror("Appointment Limit Exceeded", "The doctor has reached the maximum appointment limit for this slot and date.")
            return False

        # Check if the total appointments for the slot and date exceed the limit
        total_appointments = doctor_appointments.get(appointment_info["Doctor"], {}).get(formatted_appointment_date, 0)
        if total_appointments >= MAX_APPOINTMENTS_PER_SLOT:
            print("Doctor has reached the total appointment limit for this slot and date.")
            messagebox.showerror("Total Appointment Limit Exceeded", "The doctor has reached the total appointment limit for this slot and date.")
            return False

        if existing_count >= MAX_APPOINTMENTS_PER_SLOT:
            print("Doctor has reached the appointment limit for this slot and date.")
            messagebox.showerror("Appointment Limit Exceeded", "The doctor has reached the maximum appointment limit for this slot and date.")

            # If total appointments are still within the limit, allow the user to schedule on another date
            if total_appointments < MAX_APPOINTMENTS_PER_SLOT:
                print("User can still schedule on other dates.")
                return True
            else:
                return False

        query = "INSERT INTO appointments (patient_name, age, contact_number, sex, reason, disease, doctor, appointment_time, appointment_date, amount) " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        values = (
            appointment_info["Name"],
            appointment_info["Age"],
            appointment_info["Contact Number"],
            appointment_info["Sex"],
            appointment_info["Reason"],
            appointment_info["Disease"],
            appointment_info["Doctor"],
            appointment_info["Appointment Time"],
            formatted_appointment_date,
            appointment_info["Amount"]
        )

        # Update the doctor_appointments dictionary
        doctor = appointment_info["Doctor"]
        if doctor not in doctor_appointments:
            doctor_appointments[doctor] = {formatted_appointment_date: {appointment_info["Appointment Time"]: 1}}
        elif formatted_appointment_date not in doctor_appointments[doctor]:
            doctor_appointments[doctor][formatted_appointment_date] = {appointment_info["Appointment Time"]: 1}
        elif appointment_info["Appointment Time"] not in doctor_appointments[doctor][formatted_appointment_date]:
            doctor_appointments[doctor][formatted_appointment_date][appointment_info["Appointment Time"]] = 1
        else:
            doctor_appointments[doctor][formatted_appointment_date][appointment_info["Appointment Time"]] += 1

        cursor.execute(query, values)
        mydb.commit()
        print("Data saved successfully:", values)  # Add a debugging print statement

        # Display a success message
        messagebox.showinfo("Appointment Scheduled", "Appointment scheduled successfully!")
        return True
    except mysql.connector.Error as e:
        print("Error while inserting into the database:", str(e))
        mydb.rollback()
        messagebox.showerror("Error", "Failed to schedule the appointment. Please try again.")
        return False


login_window = None


def create_login_box(event=None):
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

    admin_login_button = tk.Button(root, borderwidth=2, relief="ridge", padx=10, pady=10, bg='lightgreen', text="Login as Admin", command=create_admin_login_box)
    admin_login_button.pack(pady=10)

    # Hide the signup_box if it exists
    if signup_box:
        signup_box.pack_forget()

    # Initialize the signup_box as None
    signup_box = None


def create_signup_box():
    global full_name_entry, age_entry, sex_var, email_entry, password_entry, signup_box
    signup_box = tk.Frame(root, borderwidth=2, relief="ridge", padx=10, pady=10)
    signup_box.pack(padx=20, pady=20)

    full_name_label = tk.Label(signup_box, text="Full Name:", anchor="w")
    full_name_label.pack()
    full_name_entry = tk.Entry(signup_box)
    full_name_entry.pack(fill="x", padx=10, pady=5)

    age_label = tk.Label(signup_box, text="Age:", anchor="w")
    age_label.pack()
    age_entry = tk.Entry(signup_box)
    age_entry.pack(fill="x", padx=10, pady=5)

    sex_label = tk.Label(signup_box, text="Sex:", anchor="w")
    sex_label.pack()
    sex_var = tk.StringVar(value="Male")
    sex_radio_male = tk.Radiobutton(signup_box, text="Male", variable=sex_var, value="Male")
    sex_radio_female = tk.Radiobutton(signup_box, text="Female", variable=sex_var, value="Female")
    sex_radio_male.pack()
    sex_radio_female.pack()

    email_label = tk.Label(signup_box, text="Email Address:", anchor="w")
    email_label.pack()
    email_entry = tk.Entry(signup_box)
    email_entry.pack(fill="x", padx=10, pady=5)

    password_label = tk.Label(signup_box, text="Password:", anchor="w")
    password_label.pack()
    password_entry = tk.Entry(signup_box, show="*")
    password_entry.pack(fill="x", padx=10, pady=5)

    create_acc_button = tk.Button(signup_box, text="Create Account", bg='lightgreen', command=signup)
    create_acc_button.pack(pady=10)

    login_page_button = tk.Label(signup_box, text="Already have an account? Log in here.", fg='blue', cursor='hand2')
    login_page_button.bind("<Button-1>", create_login_box)
    login_page_button.pack()


def is_valid_email(email):
    # Define a regular expression pattern to validate Gmail addresses
    gmail_pattern = r'^[\w\.-]+@gmail\.com$'
    return bool(re.match(gmail_pattern, email))


def create_admin_login_box():
    global admin_email_entry, admin_password_entry, admin_login_window
    admin_login_window = tk.Toplevel(root)
    admin_login_window.geometry("300x150")
    admin_login_window.title("Login as Admin")

    admin_email_label = tk.Label(admin_login_window, text="Admin Email:")
    admin_email_label.pack(anchor="w")
    admin_email_entry = tk.Entry(admin_login_window)
    admin_email_entry.pack(fill="x", padx=10, pady=5)

    admin_password_label = tk.Label(admin_login_window, text="Admin Password:")
    admin_password_label.pack(anchor="w")
    admin_password_entry = tk.Entry(admin_login_window, show="*")
    admin_password_entry.pack(fill="x", padx=10, pady=5)

    admin_login_button = tk.Button(admin_login_window, text="Login", bg='lightgreen', command=admin_accounts)
    admin_login_button.pack(pady=10)

def delete_appointment(appointment_id, cursor, connection):
    try:
        if connection:
            query = f"DELETE FROM appointments WHERE IdNo = {appointment_id}"
            cursor.execute(query)
            connection.commit()
            messagebox.showinfo("Success", "Appointment deleted successfully!")
        else:
            messagebox.showerror("Error", "Database connection is not valid.")
    except Exception as e:
        messagebox.showerror("Error", f"Error deleting appointment: {str(e)}")

def create_admin_window(cursor, mydb):
    admin_window = tk.Toplevel(root)
    admin_window.title("Admin Window")
    admin_window.geometry("700x500")  # Adjusted size

    # Create a frame for displaying appointments
    admin_frame = tk.Frame(admin_window, borderwidth=2, relief="ridge", padx=10, pady=10)
    admin_frame.pack(expand=True, fill="both")  # Allow the frame to expand

    # Add a label to display appointments
    appointments_label = tk.Label(admin_frame, text="Appointments", font=("Times", "16", "bold"))
    appointments_label.grid(row=0, column=0, columnspan=5, pady=(0, 10))  # Adjusted grid

    # Query the database to retrieve appointment information
    query = "SELECT * FROM appointments"
    cursor.execute(query)
    appointments = cursor.fetchall()

    # Create scrolled text widget to display appointment details
    text_widget = scrolledtext.ScrolledText(admin_frame, height=20, width=80, wrap=tk.WORD)
    text_widget.grid(row=1, column=0, columnspan=5, pady=(0, 10), padx=10)

    # Insert appointment information into the scrolled text widget
    for appointment in appointments:
        text_widget.insert(
            tk.END,
            f"Appointment ID: {appointment[0]}\n"
            f"Patient Name: {appointment[1]}\n"
            f"Age: {appointment[2]}\n"
            f"Contact Number: {appointment[4]}\n"
            f"Sex: {appointment[3]}\n"
            f"Reason: {appointment[5]}\n"
            f"Doctor: {appointment[6]}\n"
            f"Appointment Time: {appointment[7]}\n"
            f"Appointment Date: {appointment[8]}\n"
            f"Amount: {appointment[9]}\n"
            f"Disease: {appointment[10]}\n\n"
        )

    def delete_selected_appointment():
        selected_text = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
        lines = selected_text.split("\n")

        if len(lines) >= 2 and lines[0].startswith("Appointment ID:"):
            try:
                appointment_id = int(lines[0].split(": ")[1])
                confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this appointment?")
                if confirm:
                    delete_appointment(appointment_id, cursor, mydb)
                    refresh_appointments()
            except ValueError:
                messagebox.showerror("Error", "Invalid Appointment ID format")
        else:
            messagebox.showerror("Error", "Selected text does not contain a valid appointment")

    def refresh_appointments():
        # Clear existing text
        text_widget.delete("1.0", tk.END)

        # Query the database to retrieve updated appointment information
        cursor.execute(query)
        appointments = cursor.fetchall()

        # Insert updated appointment information into the scrolled text widget
        for appointment in appointments:
            text_widget.insert(tk.END, f"Appointment ID: {appointment[0]}\nName: {appointment[1]}\nAge: {appointment[2]}\nSex: {appointment[3]}\nContact Number: {appointment[4]}\n\n")

    # Create a button to delete selected appointment
    delete_button = tk.Button(admin_frame, text="Delete Selected Appointment", command=delete_selected_appointment, bg="lightcoral")
    delete_button.grid(row=2, column=0, pady=(10, 0), sticky="w")

    # Back button
    back_button = tk.Button(admin_frame, text="Back to Main", command=admin_window.destroy, bg="lightblue")
    back_button.grid(row=2, column=1, pady=(10, 0), sticky="w")

    # Search button
    search_button = tk.Button(admin_frame, text="Search Appointments", command=create_search_window, bg="lightgreen")
    search_button.grid(row=2, column=2, pady=(10, 0), sticky="w")

    # Logout button
    logout_button = tk.Button(admin_frame, text="Log Out", command=admin_logout, bg="lightcoral")
    logout_button.grid(row=2, column=3, pady=(10, 0), sticky="w")
    
def login():
    global email_entry, password_entry
    email = email_entry.get()
    password = password_entry.get()
    if email and password:
        if check_login_credentials(email, password):
            # Retrieve user information from the database based on the email
            query = "SELECT full_name, age, sex FROM users WHERE email = %s"
            cursor.execute(query, (email,))
            user_info = cursor.fetchone()
            
            if user_info:
                full_name, age, sex = user_info
                appointment_window(full_name, age, sex)
            else:
                messagebox.showerror("Login Failed", "Invalid email or password")
        else:
            messagebox.showerror("Login Failed", "Invalid email or password")
    else:
        messagebox.showerror("Invalid Information", "Please fill in both email and password.")


def signup():
    global full_name, age, sex
    full_name = full_name_entry.get()
    age = age_entry.get()
    
    try:
        age = int(age)  # Convert age to an integer
    except ValueError:
        messagebox.showerror("Invalid Age", "Please enter a valid age.")
        return
    
    sex = sex_var.get()
    email = email_entry.get()
    password = password_entry.get()
    
    # Rest of the code remains the same

    if full_name and age and sex and email and password:
        if insert_users_into_db(full_name, age, sex, email, password):
            messagebox.showinfo("Signup Successful", "Account created successfully!")
            appointment_window(full_name, age, sex)  # Pass user info to appointment_window
        else:
            messagebox.showerror("Signup Failed", "Failed to create an account. Please try again.")
    else:
        messagebox.showerror("Invalid Information", "Please fill in all the information needed.")


# Initialize the admin login state


admin_logged_in = False


def admin_accounts():
    global admin_logged_in
    admin_credentials = {
        "dra.dalusung@gmail.com": "admin01",
        "dra.festejo@gmail.com": "admin02",
        "dra.isip@gmail.com": "admin03",
        "dr.sutare@gmail.com": "admin04"
    }

    entered_email = admin_email_entry.get()
    entered_password = admin_password_entry.get()

    if entered_email in admin_credentials and entered_password == admin_credentials[entered_email]:
        admin_logged_in = True
        admin_window()
        admin_login_window.destroy()
    else:
        messagebox.showerror("Admin Login Failed", "Invalid email or password")

# Function to create the admin window

cursor = mydb.cursor()
def admin_window():
    global admin_logged_in
    if admin_logged_in:
        create_admin_window(cursor, mydb)
    else:
        messagebox.showerror("Admin Access Denied", "You need to log in as an admin first.")
connection=mydb.commit()


def admin_logout():
    global admin_logged_in
    admin_logged_in = False
    messagebox.showinfo("Admin Log Out", "Admin logged out successfully!")
    root.deiconify()

def open_search_window():
    create_search_window()


# Dictionary to store appointments

appointments = {}


def appointment_window(full_name, age, sex):
    # Create an appointment frame within the main window
    global appointment_window  # Declare the appointment_window as global
    global appointments  # Declare appointments as global
    global date_entry
    appointment_window = tk.Toplevel(root)
    appointment_window.geometry("500x700")
    appointment_window.title("Appointment Scheduling")

    full_name_entry.insert(0, full_name)  # Set the value of name_entry
    age_entry.insert(0, age)  # Set the value of age_entry
    sex_var.set(sex)

    # Create an appointment frame within the appointment window
    appointment_frame = tk.Frame(appointment_window, borderwidth=2, relief="ridge", padx=10, pady=10)
    appointment_frame.pack(padx=20, pady=20)

    cursor = mydb.cursor()

    # Hide the main window
    root.withdraw()

    def hide_login_box():
        login_box.place_forget()

    hide_login_box()
    
    def schedule_appointment():
        global appointments
        global date_entry
        
        patient_name = full_name_entry.get()
        patient_age = age_entry.get()
        contact_number = contact_entry.get()
        sex = sex_var.get()
        selected_doctor = doctor_var.get()
        selected_slot = slot_var.get()
        appointment_date_str = date_entry.get_date()
        selected_reason = reasons_var.get()
        disease = disease_entry.get()

        # Convert appointment_date_str from '11/10/23' to '%Y-%m-%d' format
        appointment_date_obj = datetime.strptime(appointment_date_str, '%m/%d/%y')
        formatted_appointment_date = appointment_date_obj.strftime('%Y-%m-%d')

        # Initialize amount with a default value
        amount = "Unknown"

        if selected_reason == "Checkup":
            amount = "500 pesos"
        elif selected_reason == "Medication":
            amount = "1,200 pesos"

        if full_name and patient_age and contact_number and formatted_appointment_date:
            appointment_info = {
                "Name": full_name,
                "Age": age,
                "Contact Number": contact_number,
                "Sex": sex,
                "Doctor": selected_doctor,
                "Appointment Date": formatted_appointment_date,
                "Appointment Time": selected_slot,
                "Reason": selected_reason,
                "Disease": disease,
                "Amount": amount
            }    

            # Call the function to save the appointment to the database
            if save_appointment_to_database(appointment_info):
                appointments[patient_name] = appointment_info
                # Show appointment summary
                show_appointment_summary(appointment_info)
        else:
            messagebox.showerror("Invalid Information", "Please fill in all required fields.")

    contact_label = tk.Label(appointment_window, text="Contact Number:")
    contact_label.pack()
    contact_entry = tk.Entry(appointment_window)
    contact_entry.pack()

    reasons_label = tk.Label(appointment_window, text="Reason of Appointment:")
    reasons_label.pack()
    reasons_var = tk.StringVar()
    reasons_var.set("Checkup")
    reasons_radio_checkup = tk.Radiobutton(appointment_window, text="Checkup", variable=reasons_var, value="Checkup")
    reasons_radio_medication = tk.Radiobutton(appointment_window, text="Medication", variable=reasons_var, value="Medication")
    reasons_radio_checkup.pack()
    reasons_radio_medication.pack()

    disease_label = tk.Label(appointment_window, text="Patient's Disease:")
    disease_label.pack()
    disease_entry = tk.Entry(appointment_window)
    disease_entry.pack()


    # Create a dictionary to store doctors and their available slots
    doctors = {
        "Dra. Dalusung": ["9:00 AM - 10:00 AM", "2:00 PM - 3:00 PM"],
        "Dra. Festejo": ["10:00 AM - 11:00 AM", "3:00 PM - 4:00 PM"],
        "Dra. Isip": ["7:00 AM - 8:00 AM", "5:00 PM - 6:00 PM"],
        "Dr. Sutare": ["11:00 AM - 12:00 PM", "7:00 PM - 8:00 PM"],
        }

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

    date_label = tk.Label(appointment_window, text="Appointment Date:")
    date_label.pack()
    date_entry = Calendar(appointment_window, selectmode="day", year=2023, month=1, day=1)
    date_entry.pack()

    schedule_button = tk.Button(appointment_window, text="Schedule Appointment Summary", command=schedule_appointment)
    schedule_button.pack()

    # Make sure to destroy the appointment frame properly when it's closed
    appointment_window.protocol("WM_DELETE_WINDOW", show_main_window)
    appointment_window.mainloop()

    root.withdraw()

    # Insert the setup_tree_widget function to display the tree widget
    setup_tree_widget()

    def hide_login_box():
        login_box.place_forget()

    hide_login_box()


def close_appointment_window():
    appointment_window.destroy()



def show_appointment_summary(appointment_info):
    def update_appointment():
        global update_window
        global summary_window
        update_window = tk.Toplevel(root)
        update_window.geometry("500x400")
        update_window.title("Update Appointment")

        # Create entry widgets for each field to allow editing
        updated_info = {}
        for index, (key, value) in enumerate(appointment_info.items(), start=1):
            label = tk.Label(update_window, text=f"{key}:", font=("Arial", 12, "bold"))
            label.grid(row=index, column=0, pady=5, padx=10, sticky="w")

            entry = tk.Entry(update_window, font=("Arial", 12))
            entry.insert(0, value)
            entry.grid(row=index, column=1, pady=5, padx=10, sticky="e")
            updated_info[key] = entry

        # Function to update the appointment in the database
        def save_updated_appointment():
            update_dict = {key: entry.get() if hasattr(entry, 'get') else entry for key, entry in updated_info.items()}

            # Convert values to appropriate data types
            if 'Appointment ID' in appointment_info:
                update_values = (
                    str(update_dict["Name"]),  # Assuming patient_name is a string
                    int(update_dict["Age"]),    # Assuming age is an integer
                    str(update_dict["Contact Number"]),  # Assuming contact_number is a string
                    str(update_dict["Sex"]),    # Assuming sex is a string
                    str(update_dict["Reason"]),  # Assuming reason is a string
                    str(update_dict["Disease"]),  # Assuming disease is a string
                    str(update_dict["Doctor"]),  # Assuming doctor is a string
                    str(update_dict["Appointment Time"]),  # Assuming appointment_time is a string
                    str(update_dict["Appointment Date"]),  # Assuming appointment_date is a string
                    str(update_dict["Amount"]),  # Assuming amount is a float
                    int(appointment_info["Appointment ID"])  # Assuming Appointment ID is an integer
                )

                # Update the database with the modified information
                update_query = "UPDATE `appointments` SET `IdNo`=%s,`Patient_Name`=%s,`Age`=%s,`Contact_Number`=%s,`Sex`=%s',`Reason`=%s,`Doctor`=%s,`Appointment_Time`=%s,`Appointment_Date`=%s,`Amount`=%s,`Disease`=%s WHERE 'idno'=%s"

                try:
                    print("Executing update query:", update_query)
                    print("Update values:", update_values)

                    cursor.execute(update_query, update_values)
                    mydb.commit()
                    print("Database update successful!")

                    messagebox.showinfo("Update Successful", "Appointment updated successfully!")
                    update_window.destroy()
                except mysql.connector.Error as e:
                    print("Error while updating the database:", str(e))
                    mydb.rollback()
                    messagebox.showerror("Error", "Failed to update the appointment. Please try again.")
            else:
                print("Error: 'Appointment ID' not found in appointment_info")

        # Create the "Save Updated Appointment" button
        save_updated_appointment_button = tk.Button(update_window, text="Save Updated Appointment", command=save_updated_appointment, bg="green", fg="white", font=("Arial", 12))
        save_updated_appointment_button.grid(row=len(updated_info) + 1, column=1, pady=10)

        # Create a "Print PDF" button
        print_pdf_button = tk.Button(update_window, text="Print PDF", command=lambda: print_to_pdf(updated_info), bg="blue", fg="white", font=("Arial", 12))
        print_pdf_button.grid(row=len(updated_info) + 2, column=1, pady=10)


        def print_to_pdf(appointment_info):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            # Add information to the PDF
            for key, value in appointment_info.items():
                pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)

            # Ask the user to select a directory for saving the PDF
            file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])

            if file_path:
                # Save the PDF file with the user-selected path
                pdf.output(file_path)
                messagebox.showinfo("PDF Created", f"Appointment summary saved as PDF in {file_path}")
            else:
                messagebox.showinfo("PDF Creation Canceled", "PDF creation was canceled by the user.")


        # Create a delete button to delete the appointment from the database
        def delete_appointment():
            delete_query = "DELETE FROM appointments WHERE IdNo=%s"
            delete_values = (int(appointment_info["Appointment ID"]),)

            try:
                cursor.execute(delete_query, delete_values)
                mydb.commit()
                messagebox.showinfo("Delete Successful", "Appointment deleted successfully!")
                update_window.destroy()
            except mysql.connector.Error as e:
                print("Error while deleting the appointment:", str(e))
                mydb.rollback()
                messagebox.showerror("Error", "Failed to delete the appointment. Please try again.")
    
    summary_window = tk.Toplevel(root)
    summary_window.geometry("700x500")
    summary_window.title("Appointment Summary")

    for index, (key, value) in enumerate(appointment_info.items(), start=1):
        if key == "Appointment Date":
            formatted_date = value.split()[0]
            label = tk.Label(summary_window, text=f"{key}:", font=("Arial", 12))
            value_label = tk.Label(summary_window, text=f"{formatted_date}", font=("Arial", 12))
        else:
            label = tk.Label(summary_window, text=f"{key}:", font=("Arial", 12))
            value_label = tk.Label(summary_window, text=f"{value}", font=("Arial", 12))
        label.grid(row=index, column=0, pady=5, padx=10, sticky="w")
        value_label.grid(row=index, column=1, pady=5, padx=10, sticky="w")

    # Create an "Update Appointment" button
    update_appointment_button = tk.Button(summary_window, text="Update Appointment", command=update_appointment, bg="lightgreen", fg="black", font=("Arial", 12))
    update_appointment_button.grid(row=len(appointment_info) + 1, column=0, pady=10, padx=10, sticky="w")

    # Create a button to print and save the summary
    print_summary_button = tk.Button(summary_window, text="Print Summary and Save to File", command=lambda: save_summary_to_file(appointment_info), bg="lightgreen", fg="black", font=("Arial", 12))
    print_summary_button.grid(row=len(appointment_info) + 1, column=1, pady=10, padx=10, sticky="w")

    # Create a "Cancel Appointment" button
    cancel_button = tk.Button(summary_window, text="Cancel Appointment", command=cancel_appointment, bg="red", fg="white", font=("Arial", 12))
    cancel_button.grid(row=len(appointment_info) + 2, column=0, pady=10, padx=10, sticky="w")

    # Create a "Close System" button
    close_system_button = tk.Button(summary_window, text="Close System", command=stop_system, bg="gray", fg="white", font=("Arial", 12))
    close_system_button.grid(row=len(appointment_info) + 2, column=1, pady=10, padx=10, sticky="w")


# Add this function to handle appointment cancellation
def cancel_appointment(appointment_info, summary_window):
    result = messagebox.askquestion("Cancel Appointment", "Are you sure you want to cancel this appointment?")
    
    if result == "yes":
        # Retrieve the appointment ID from the appointment_info dictionary
        appointment_id = appointment_info.get("Appointment ID")

        if appointment_id is not None:
            # Delete the appointment from the database
            delete_query = "DELETE FROM appointments WHERE IdNo=%s"
            delete_values = (appointment_id,)

            try:
                cursor.execute(delete_query, delete_values)
                mydb.commit()
                messagebox.showinfo("Appointment Canceled", "The appointment has been canceled.")
                summary_window.destroy()
            except mysql.connector.Error as e:
                print("Error while canceling the appointment:", str(e))
                mydb.rollback()
                messagebox.showerror("Error", "Failed to cancel the appointment. Please try again.")
        else:
            messagebox.showerror("Error", "Appointment ID not found.")


# Create a dictionary to store doctors and their available slots
doctors = {
    "Dra. Dalusung": ["9:00 AM - 10:00 AM", "2:00 PM - 3:00 PM"],
    "Dra. Festejo": ["10:00 AM - 11:00 AM", "3:00 PM - 4:00 PM"],
    "Dra. Isip": ["7:00 AM - 8:00 AM", "5:00 PM - 6:00 PM"],
    "Dr. Sutare": ["11:00 AM - 12:00 PM", "7:00 PM - 8:00 PM"],
}
def stop_system():
    root.destroy()

def create_search_window():
    global search_date_entry, search_time_var, search_doctor_var, search_results_tree
    search_window = tk.Toplevel(root)
    search_window.geometry("1220x500")
    search_window.title("Search Appointments")

    search_date_label = tk.Label(search_window, text="Search by Date:")
    search_date_label.grid(row=0, column=0, padx=10, pady=5)
    search_date_entry = tk.Entry(search_window)  # Declare as a global variable
    search_date_entry.grid(row=0, column=1, padx=10, pady=5)

    search_doctor_label = tk.Label(search_window, text="Search by Doctor:")
    search_doctor_label.grid(row=1, column=0, padx=10, pady=5)
    search_doctor_var = tk.StringVar(value="")
    search_doctor_option_menu = tk.OptionMenu(search_window, search_doctor_var, "", *doctors.keys())
    search_doctor_option_menu.grid(row=1, column=1, padx=10, pady=5)

    search_time_label = tk.Label(search_window, text="Search by Time:")
    search_time_label.grid(row=2, column=0, padx=10, pady=5)
    search_time_var = tk.StringVar(value="")  # Set a default value
    search_time_option_menu = tk.OptionMenu(search_window, search_time_var, "")  # Initially empty
    search_time_option_menu.grid(row=2, column=1, padx=10, pady=5)

    # Function to update time options based on selected doctor
    def update_time_options(*args):
        selected_doctor = search_doctor_var.get()
        search_time_option_menu['menu'].delete(0, 'end')  # Clear the current time options
        if selected_doctor in doctors:
            for slot in doctors[selected_doctor]:
                search_time_option_menu['menu'].add_command(label=slot, command=tk._setit(search_time_var, slot))

    # Attach the update_time_options function to the doctor_var
    search_doctor_var.trace("w", update_time_options)

    search_button = tk.Button(search_window, text="Search Appointments", command=search_appointments)
    search_button.grid(row=3, column=0, columnspan=2, pady=10)

    # Create a treeview widget to display search results
    search_results_tree = ttk.Treeview(search_window, columns=("Name", "Date", "Time", "Doctor", "Reason"))
    search_results_tree.heading("#1", text="Name")
    search_results_tree.heading("#2", text="Date")
    search_results_tree.heading("#3", text="Time")
    search_results_tree.heading("#4", text="Doctor")
    search_results_tree.heading("#5", text="Reason")
    search_results_tree.grid(row=4, column=0, columnspan=2, padx=10, pady=5)

    # Add scrollbars to the treeview for better navigation
    scrollbar_x = ttk.Scrollbar(search_window, orient="horizontal", command=search_results_tree.xview)
    scrollbar_x.grid(row=5, column=0, columnspan=2, sticky="ew")
    search_results_tree.configure(xscrollcommand=scrollbar_x.set)
    scrollbar_y = ttk.Scrollbar(search_window, orient="vertical", command=search_results_tree.yview)
    scrollbar_y.grid(row=4, column=2, sticky="ns")
    search_results_tree.configure(yscrollcommand=scrollbar_y.set)

    search_results_tree.grid()

    search_window.protocol("WM_DELETE_WINDOW", search_window.destroy)
    search_window.mainloop()


# Create a function to set up and populate the tree widget
def setup_tree_widget():
    # Create a new window or frame to contain the tree widget
    tree_window = tk.Toplevel(root)
    tree_window.title("Appointments List")

    # Create the Treeview widget
    tree = ttk.Treeview(tree_window, columns=("Name", "Age", "Contact Number", "Doctor", "Appointment Date", "Reason", "Disease"))

    # Define column names
    tree.heading("#1", text="Name")
    tree.heading("#2", text="Doctor")
    tree.heading("#3", text="Appointment Date")
    tree.heading("#4", text="Reason")

    # Insert data into the tree widget
    # For each appointment, insert the data into the tree widget
    for name, doctor, appointment_date, reason, amount in appointments:
        tree.insert("", "end", values=(name, doctor, appointment_date, reason))

    # Pack the tree widget
    tree.pack()


def search_appointments():
    search_date = search_date_entry.get()
    search_time = search_time_var.get()
    search_doctor = search_doctor_var.get()

    try:
        query = "SELECT * FROM appointments WHERE 1"
        params = []  # Create a list to store the search parameters

        if search_date:
            query += " AND appointment_date = %s"
            params.append(search_date)

        if search_time:
            query += " AND appointment_time = %s"
            params.append(search_time)

        if search_doctor:
            query += " AND doctor = %s"
            params.append(search_doctor)

        cursor.execute(query, tuple(params))  # Convert the params list to a tuple
        results = cursor.fetchall()

        if results:
            show_search_results(results)
        else:
            messagebox.showinfo("Search Results", "No appointments found for the given criteria.")
    except Exception as e:
        print("Error while searching for appointments:", str(e))


def show_search_results(results):
    search_results_tree.delete(*search_results_tree.get_children())  # Clear existing items in the tree
    for result in results:
        search_results_tree.insert("", "end", values=(result[1], result[8], result[7], result[6], result[5]))


def doctor_window():
    doctor_window = tk.Toplevel()
    doctor_window.title("Doctor Appointment Page")

    doctor_frame = tk.Frame(doctor_window)
    doctor_frame.pack()

    doctor_id = "your_doctor_id_here"  # Replace with the actual doctor's ID

    appointments = get_appointments_for_doctor(doctor_id)  # Fetch appointments for the given doctor_id

    if appointments:
        for appointment in appointments:
            appointment_label = tk.Label(doctor_frame, text=f"Patient: {appointment[1]}, Date: {appointment[7]}, Time: {appointment[6]}")
            appointment_label.pack()
    else:
        no_appointments_label = tk.Label(doctor_frame, text="No appointments for this doctor.")
        no_appointments_label.pack()

    logout_button = tk.Button(doctor_window, text="Log Out", command=doctor_window.destroy)
    logout_button.pack()

    doctor_window.mainloop()

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Appointment Summary', 0, 1, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

def save_summary_to_file(appointment_info):
    # Open a file dialog to choose the save location and filename
    file_path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                               filetypes=[("PDF files", "*.pdf")],
                                               title="Save Appointment Summary As")

    if file_path:
        try:
            pdf = PDF()
            pdf.add_page()

        
            pdf.chapter_body("______________________________________________________________________________")

            # Write appointment information to PDF
            for key, value in appointment_info.items():
                pdf.chapter_body(f"{key}: {value}")

            pdf.output(file_path)
            messagebox.showinfo("Save Successful", "Appointment summary saved successfully!")
        except Exception as e:
            print("Error while saving appointment summary:", str(e))
            messagebox.showerror("Save Error", "Failed to save appointment summary.")


def show_main_window():
    # Show the main window again
    root.deiconify()

    # Create a new search window when "Search Appointments" is clicked
    create_search_window()

# Create the main window


root = tk.Tk()
root.geometry("700x500")
root.title("Hospital Management System")


# Load and display the background image
background_image = Image.open("D:/Nykhole's Files - Copy/[ALL] BSU - SECOND YEAR/FILES/ADV. COMPROG/HMS_DB/final.jpg")
background_image = background_image.resize((1365, 750), Image.Resampling.NEAREST)
background_photo = ImageTk.PhotoImage(background_image)

background_label = tk.Label(root, image=background_photo)
background_label.place(x=0, y=0, relwidth=1, relheight=1)


label = tk.Label(root,
                 text="TCNR's Hospital Management System",
                 font=("Times", "24", "bold"),
                 fg="red",
                 )
label.pack(padx=50, pady=10)

label = tk.Label(root,
                 text="REGISTRATION FORM:",
                 font=("Times", "14"),
                 fg="black",bg='white'
                 )
label.pack(padx=50, pady=10)

# initialize login_box frame but hide it
login_box = tk.Frame(root, borderwidth=2, relief="ridge", padx=10, pady=10)
login_box.pack()
login_box.place_forget()  # Hide the login form initially
create_signup_box()


root.mainloop()
mydb.close()