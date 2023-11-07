import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import mysql.connector
from tkinter import ttk  # for tree
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import re


# Maximum appointments per doctor
MAX_APPOINTMENTS_PER_DOCTOR = 20  # You can adjust this value as needed


# Declare global variables
search_date_entry = None
search_time_var = None
search_doctor_var = None

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
        query = "SELECT * FROM appointments WHERE doctor_id = %s"
        cursor.execute(query, (doctor_id,))
        appointments = cursor.fetchall()
        return appointments
    except Exception as e:
        print("Error while retrieving doctor appointments:", str(e))
        return None


def save_appointment_to_database(appointment_info):
    try:
        query = "INSERT INTO appointments (patient_name, age, contact_number, sex, reason, doctor, appointment_time, appointment_date, amount) " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        values = (
            appointment_info["Name"],
            appointment_info["Age"],
            appointment_info["Contact Number"],
            appointment_info["Sex"],
            appointment_info["Reason"],
            appointment_info["Doctor"],
            appointment_info["Appointment Time"],
            appointment_info["Appointment Date"],
            appointment_info["Amount"]
        )

        # Check doctor appointment count here
        doctor = appointment_info["Doctor"]
        if doctor in doctor_appointments:
            if len(doctor_appointments[doctor]) > MAX_APPOINTMENTS_PER_DOCTOR:
                print("Doctor has reached the appointment limit.")
                messagebox.showerror("Appointment Limit Exceeded", "The doctor has reached the maximum appointment limit.")
                return False

        cursor.execute(query, values)
        mydb.commit()
        print("Data saved successfully:", values)  # Add a debugging print statement

        # Add the appointment to the doctor's list
        if doctor not in doctor_appointments:
            doctor_appointments[doctor] = [appointment_info]
        else:
            doctor_appointments[doctor].append(appointment_info)

        # Display a success message
        messagebox.showinfo("Appointment Scheduled", "Appointment scheduled successfully!")
        return True
    except mysql.connector.Error as e:
        print("Error while inserting into the database:", str(e))
        mydb.rollback()
        messagebox.showerror("Error", "Failed to schedule the appointment. Please try again.")
        return False



login_window = None


################################################################################################


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
    global username_entry, email_entry, password_entry, signup_box
    signup_box = tk.Frame(root, borderwidth=2, relief="ridge", padx=10, pady=10)
    signup_box.pack(padx=20, pady=20)

    username_label = tk.Label(signup_box, text="Username:", anchor="w")
    username_label.pack()
    username_entry = tk.Entry(signup_box)
    username_entry.pack(fill="x", padx=10, pady=5)

    email_label = tk.Label(signup_box, text="Email Address:", anchor="w")
    email_label.pack()
    email_entry = tk.Entry(signup_box)
    email_entry.pack(fill="x", padx=10, pady=5)

    password_label = tk.Label(signup_box, text="Password:", anchor="w")
    password_label.pack()
    password_entry = tk.Entry(signup_box, show="*")
    password_entry.pack(fill="x", padx=10, pady=5)

    def signup():
        username = username_entry.get()
        email = email_entry.get()
        password = password_entry.get()

        if not is_valid_email(email):
            # Show an error message and do not proceed with signup
            error_message = tk.Label(signup_box, text="Invalid email address. Please use a valid Gmail address.")
            error_message.pack()
        else:
            create_login_box()

           
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


def create_admin_window():
    admin_window = tk.Toplevel(root)
    admin_window.title("Admin Window")

    # Create a frame for displaying user accounts and records
    admin_frame = tk.Frame(admin_window, borderwidth=2, relief="ridge", padx=10, pady=10)
    admin_frame.pack(padx=20, pady=20)

    # Add a label to display user accounts and records
    user_accounts_label = tk.Label(admin_frame, text="User Accounts and Records", font=("Times", "16", "bold"))
    user_accounts_label.pack()

    # Query the database to retrieve user accounts and records
    query = "SELECT * FROM users"
    cursor.execute(query)
    user_accounts = cursor.fetchall()

    # Create a text widget to display user accounts and records
    text_widget = tk.Text(admin_frame, height=10, width=50)
    text_widget.pack()

    # Insert user accounts and records into the text widget
    for user_account in user_accounts:
        text_widget.insert(tk.END, f"Username: {user_account[0]}\nEmail: {user_account[1]}\nPassword: {user_account[2]}\n\n")

    # summary of appointments

    search_button = tk.Button(admin_frame, text="Search Appointments", command=create_search_window)
    search_button.pack()

    # logout button
    logout_button = tk.Button(admin_window, text="Log Out", command=admin_logout)
    logout_button.pack()

    # Create a button to go back to the main window
    back_button = tk.Button(admin_frame, text="Back to Main", command=admin_window.destroy)
    back_button.pack()


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


def admin_window():
    global admin_logged_in
    if admin_logged_in:
        create_admin_window()
    else:
        messagebox.showerror("Admin Access Denied", "You need to log in as an admin first.")


def admin_logout():
    global admin_logged_in
    admin_logged_in = False
    messagebox.showinfo("Admin Log Out", "Admin logged out successfully!")
    root.deiconify()

# Dictionary to store appointments


appointments = {}


def appointment_window():
    # Create an appointment frame within the main window
    global appointment_window  # Declare the appointment_window as global
    global appointments  # Declare appointments as global
    appointment_window = tk.Toplevel(root)
    appointment_window.geometry("700x500")
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
        global appointments
        patient_name = name_entry.get()
        age = age_entry.get()
        contact_number = contact_entry.get()
        sex = sex_var.get()
        selected_doctor = doctor_var.get()
        selected_slot = slot_var.get()
        appointment_date = date_entry.get()
        selected_reason = reasons_var.get()

        # Initialize amount with a default value
        amount = "Unknown"

        if selected_reason == "Checkup":
            amount = "500 pesos"
        elif selected_reason == "Medication":
            amount = "1,200 pesos"

        if patient_name and age and contact_number and appointment_date:
            appointment_info = {
                "Name": patient_name,
                "Age": age,
                "Contact Number": contact_number,
                "Sex": sex,
                "Doctor": selected_doctor,
                "Appointment Date": appointment_date,
                "Appointment Time": selected_slot,
                "Reason": selected_reason,
                "Amount": amount
            }  

            # Check doctor appointment count here
        doctor = appointment_info["Doctor"]
        if doctor in doctor_appointments:
            if len(doctor_appointments[doctor]) >= MAX_APPOINTMENTS_PER_DOCTOR:
                # Handle the case where the maximum appointments for the doctor is reached
                # You can show an error message or take appropriate action
                messagebox.showerror("Doctor Appointment Limit", f"The doctor {doctor} has reached the maximum appointment limit.")
                return
            else:
                # The doctor can still accept more appointments
                # Add the appointment to the doctor's list
                doctor_appointments[doctor].append(appointment_info)
        else:
            # The doctor is not in the dictionary, so add them with the first appointment
            doctor_appointments[doctor] = [appointment_info]

        # Call the function to save the appointment to the database
        if save_appointment_to_database(appointment_info):
            appointments[patient_name] = appointment_info
            # Show appointment summary
            show_appointment_summary(appointment_info)
        else:
            messagebox.showerror("Invalid Information", "Please fill in all required fields.")

            # Call the function to save the appointment to the database
            if save_appointment_to_database(appointment_info):
                appointments[patient_name] = appointment_info
                # Show appointment summary
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

    schedule_button = tk.Button(appointment_window, text="Schedule Appointment and Print Summary", command=schedule_appointment)
    schedule_button.pack()

    # Create a button to go back to the main window
    back_button = tk.Button(appointment_frame, text="Back to Main", command=show_main_window)
    back_button.pack()

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

# Function to generate PDF report
def generate_pdf_report(appointment_info):
    pdf_filename = "appointment_summary.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=letter)

    # Set the title for the PDF
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "Appointment Summary")

    # Add appointment information to the PDF
    c.setFont("Helvetica", 12)
    y_coordinate = 700
    for key, value in appointment_info.items():
        appointment_text = f"{key}: {value}"
        c.drawString(100, y_coordinate, appointment_text)
        y_coordinate -= 20

    # Save the PDF
    c.showPage()
    c.save()

    # Display a message when the PDF is generated
    messagebox.showinfo("PDF Generated", "Appointment summary PDF generated successfully!")

# Function to generate the PDF report
def generate_pdf_report(appointment_info):
    # Your PDF generation code here

# Function to handle the "Print as PDF" button click
    def print_as_pdf():
        generate_pdf_report(appointment_info)
        messagebox.showinfo("PDF Generated", "Appointment summary PDF generated successfully!")

# Function to display appointment summary
def show_appointment_summary(appointment_info):
    summary_window = tk.Toplevel(root)
    summary_window.geometry("700x500")
    summary_window.title("Appointment Summary")

    for key, value in appointment_info.items():
        if key == "Appointment Date":
            # Format the date to display only the date portion (e.g., 2023-01-01)
            formatted_date = value.split()[0]
            label = tk.Label(summary_window, text=f"{key}: {formatted_date}")
        else:
            label = tk.Label(summary_window, text=f"{key}: {value}")
        label.pack()

    # Insert the appointment information into the database
    query = "INSERT INTO appointments (patient_name, age, contact_number, sex, reason, doctor, appointment_time, appointment_date, amount) " \
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(query, (patient_name, age, contact_number, sex, selected_reason, selected_doctor, appointment_time, appointment_date, amount))
    mydb.commit()

    # Generate a PDF report for the appointment
    generate_pdf_report(appointment_info)

    # Close the appointment window after displaying the summary
    appointment_window.destroy()
    root.deiconify()

#################################################################################################

# Create a dictionary to store doctors and their available slots


doctors = {
    "Dra. Dalusung": ["9:00 AM - 10:00 AM", "2:00 PM - 3:00 PM"],
    "Dra. Festejo": ["10:00 AM - 11:00 AM", "3:00 PM - 4:00 PM"],
    "Dra. Isip": ["7:00 AM - 8:00 AM", "5:00 PM - 6:00 PM"],
    "Dr. Sutare": ["11:00 AM - 12:00 PM", "7:00 PM - 8:00 PM"],
}


def create_search_window():
    global search_date_entry, search_time_var, search_doctor_var, search_results_tree
    search_window = tk.Toplevel(root)
    search_window.geometry("400x400")
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

########################### SEARCH ####################################################

# Create a function to set up and populate the tree widget
def setup_tree_widget():
    # Create a new window or frame to contain the tree widget
    tree_window = tk.Toplevel(root)
    tree_window.title("Appointments List")

    # Create the Treeview widget
    tree = ttk.Treeview(tree_window, columns=("Name", "Age", "Contact Number", "Doctor", "Appointment Date", "Reason"))

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