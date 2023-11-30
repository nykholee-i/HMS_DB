import tkinter as tk
from tkinter import messagebox, scrolledtext
from PIL import Image, ImageTk
import mysql.connector
from tkinter import ttk, filedialog  # for tree
from tkcalendar import Calendar
from datetime import datetime
from fpdf import FPDF
from collections import defaultdict
from tkinter import PhotoImage
import re  # for pdf data or doctor limits

# Maximum appointments per doctor's slot
MAX_APPOINTMENTS_PER_SLOT = 2

# Declare global variables
search_date_entry = None
search_time_var = None
search_doctor_var = None
date_entry = None
full_name_entry = None

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
    database="hms"
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
        query = "SELECT doctor, appointment_time, appointment_date FROM appointments"
        cursor.execute(query)
        appointments = cursor.fetchall()

        for appointment in appointments:
            doctor = appointment[0]
            slot = appointment[1]
            date = appointment[2]

            if date not in doctor_appointments[doctor]:
                doctor_appointments[doctor][date] = {slot: 1}
            elif slot not in doctor_appointments[doctor][date]:
                doctor_appointments[doctor][date][slot] = 1
            else:
                doctor_appointments[doctor][date][slot] += 1
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


def show_main_window_callback():
    root.deiconify()


def create_login_box():
    global email_entry, password_entry, login_window, root

    # Hide the main window
    root.iconify()

    login_window = tk.Toplevel()
    login_window.title("Login as User")
    login_window.geometry("500x550")

    # Background Image
    background_image = Image.open("D:/Nykhole's Files - Copy/[ALL] BSU - SECOND YEAR/FILES/ADV. COMPROG/HMS_DB/login.png")
    background_image = background_image.resize((500, 550), Image.Resampling.NEAREST)
    background_photo = ImageTk.PhotoImage(background_image)

    background_label = tk.Label(login_window, image=background_photo)
    background_label.place(x=0, y=0, relwidth=1, relheight=1)
    background_label.image = background_photo

    # Add space at the top before the login information
    top_space_label = tk.Label(login_window, text="Login", font=("Arial", 15, "bold"), bg="white")
    top_space_label.pack(pady=10)

    # Logo Image
    logo_image = Image.open("D:/Nykhole's Files - Copy/[ALL] BSU - SECOND YEAR/FILES/ADV. COMPROG/HMS_DB/logo.png")
    logo_image = logo_image.resize((150, 150), Image.Resampling.NEAREST)
    logo_photo = ImageTk.PhotoImage(logo_image)

    # Display the logo
    logo_label = tk.Label(login_window, image=logo_photo, bg='white')
    logo_label.image = logo_photo
    logo_label.pack()

    def make_label_transparent(label):
        label.configure(bg="white")

    email_label = tk.Label(login_window, text="Email Address:", anchor="w", justify="center", bg='white', font=("Arial", 12))
    email_label.pack(pady=10)
    make_label_transparent(email_label)
    email_entry = tk.Entry(login_window, font=("Arial", 12))
    email_entry.pack(pady=10, ipadx=10)

    password_label = tk.Label(login_window, text="Password:", anchor="w", justify="center", bg='white', font=("Arial", 12))
    password_label.pack(pady=10)
    make_label_transparent(password_label)
    password_entry = tk.Entry(login_window, show="*", font=("Arial", 12))
    password_entry.pack(pady=10, ipadx=10)

    login_button = tk.Button(login_window, text="Login", command=login, bg="yellowgreen", font=("Arial", 12))
    login_button.pack(pady=10)

    def back_to_main():
        login_window.destroy()
        root.deiconify()

    back_button = tk.Button(login_window, text="Close", command=back_to_main, bg="gray", font=("Arial", 12))
    back_button.pack(pady=10)

    login_window.mainloop


# Callback function to show the main window again
def show_main_window_callback():
    global login_window
    if login_window:
        login_window.destroy()  # Destroy the login window instead of hiding it
    root.deiconify()


def create_signup_box():
    global full_name_entry, age_entry, sex_var, email_entry, password_entry, signup_box, root

    # Hide the main window
    root.iconify()

    signup_box = tk.Toplevel()
    signup_box.title("Sign Up")
    signup_box.geometry("550x700")

    # Background Image
    background_image = Image.open("D:/Nykhole's Files - Copy/[ALL] BSU - SECOND YEAR/FILES/ADV. COMPROG/HMS_DB/signup.png")
    background_image = background_image.resize((550, 700), Image.Resampling.NEAREST)
    background_photo = ImageTk.PhotoImage(background_image)
    background_label = tk.Label(signup_box, image=background_photo)
    background_label.place(x=0, y=0, relwidth=1, relheight=1)
    background_label.image = background_photo

    # Add space at the top before the login information
    top_space_label = tk.Label(signup_box, text="Sign Up", font=("Arial", 15, "bold"), bg="white")
    top_space_label.pack(pady=10)

    # Logo Image
    logo_image = Image.open("D:/Nykhole's Files - Copy/[ALL] BSU - SECOND YEAR/FILES/ADV. COMPROG/HMS_DB/logo.png")
    logo_image = logo_image.resize((150, 150), Image.Resampling.NEAREST)
    logo_photo = ImageTk.PhotoImage(logo_image)
    logo_label = tk.Label(signup_box, image=logo_photo, bg='white')
    logo_label.image = logo_photo
    logo_label.pack()

    signup_box.configure(bg="lavender")

    def make_label_transparent(label):
        label.configure(bg="white")

    full_name_label = tk.Label(signup_box, text="Full Name:", anchor="w", bg='white', font=("Arial", 12))
    full_name_label.pack(pady=5)
    make_label_transparent(full_name_label)
    full_name_entry = tk.Entry(signup_box, font=("Arial", 12))
    full_name_entry.pack(pady=5)

    age_label = tk.Label(signup_box, text="Age:", anchor="w", bg='white', font=("Arial", 12))
    age_label.pack(pady=5)
    make_label_transparent(age_label)
    age_var = tk.StringVar()
    age_entry = tk.Entry(signup_box, textvariable=age_var, width=8, font=("Arial", 12))
    age_entry.pack(pady=10, ipadx=2)

    def validate_age_input(input_text):
        if input_text.isdigit() or input_text == "":
            return True
        else:
            messagebox.showerror("Invalid Age", "Please enter only numeric values for the age.")
            return False

    validate_age_input_cmd = signup_box.register(validate_age_input)
    age_entry.configure(validate="key", validatecommand=(validate_age_input_cmd, "%P"))

    sex_label = tk.Label(signup_box, text="Sex:", anchor="w", bg='lavender', font=("Arial", 12))
    sex_label.pack(pady=5)
    make_label_transparent(sex_label)
    sex_var = tk.StringVar(value="Male")
    sex_radio_male = tk.Radiobutton(signup_box, text="Male", variable=sex_var, value="Male", bg='lavender', font=("Arial", 12))
    sex_radio_female = tk.Radiobutton(signup_box, text="Female", variable=sex_var, value="Female", bg='lavender', font=("Arial", 12))
    make_label_transparent(sex_radio_male)
    make_label_transparent(sex_radio_female)
    sex_radio_male.pack(pady=5)
    sex_radio_female.pack(pady=5)

    email_label = tk.Label(signup_box, text="Email Address:", anchor="w", bg='lavender', font=("Arial", 12))
    email_label.pack(pady=5)
    make_label_transparent(email_label)
    email_entry = tk.Entry(signup_box, font=("Arial", 12))
    email_entry.pack(pady=5)

    password_label = tk.Label(signup_box, text="Password:", anchor="w", bg='lavender', font=("Arial", 12))
    password_label.pack(pady=5)
    make_label_transparent(password_label)
    password_entry = tk.Entry(signup_box, show="*", font=("Arial", 12))
    password_entry.pack(pady=5)

    create_acc_button = tk.Button(signup_box, text="Create Account", bg='yellowgreen', command=signup, font=("Arial", 12))
    create_acc_button.pack(pady=10)

    def back_to_main():
        signup_box.destroy()
        root.deiconify()

    back_button = tk.Button(signup_box, text="Close", command=back_to_main, bg="gray", font=("Arial", 12))
    back_button.pack(pady=10)

    signup_box.mainloop()


def show_main_window():
    root.deiconify()

def close_signup_box():
    signup_box.destroy()
    show_main_window()


def is_valid_email(email):
    # Define a regular expression pattern to validate Gmail addresses
    gmail_pattern = r'^[\w\.-]+@gmail\.com$'
    return bool(re.match(gmail_pattern, email))

# Callback function to show the main window again
def show_main_window_callback():
    root.deiconify()


def create_admin_login_box():
    global admin_email_entry, admin_password_entry, admin_login_box, root  # Add root to the global variables
    # Hide the main window
    root.iconify()

    admin_login_box = tk.Toplevel()
    admin_login_box.title("Admin Login")
    admin_login_box.geometry("500x550")

    # Background Image
    background_image = Image.open("D:Nykhole's Files - Copy/[ALL] BSU - SECOND YEAR/FILES/ADV. COMPROG/HMS_DB/login.png")
    background_image = background_image.resize((500, 550), Image.Resampling.NEAREST)
    background_photo = ImageTk.PhotoImage(background_image)

    background_label = tk.Label(admin_login_box, image=background_photo)
    background_label.place(x=0, y=0, relwidth=1, relheight=1)

    # Keep a reference to the image to prevent garbage collection
    background_label.image = background_photo

    top_space_label = tk.Label(admin_login_box, text="Admin Login", font=("Arial", 15, "bold"), bg="white")
    top_space_label.pack(pady=10)

    # Logo Image
    logo_image = Image.open("D:/Nykhole's Files - Copy/[ALL] BSU - SECOND YEAR/FILES/ADV. COMPROG/HMS_DB/logo.png")  # Replace with the path to your logo
    logo_image = logo_image.resize((150, 150), Image.Resampling.NEAREST)  # Adjust size as needed
    logo_photo = ImageTk.PhotoImage(logo_image)

    # Display the logo
    logo_label = tk.Label(admin_login_box, image=logo_photo, bg='white')
    logo_label.image = logo_photo
    logo_label.pack()

    def make_label_transparent(label):
        label.configure(bg="white")

    admin_email_label = tk.Label(admin_login_box, text="Admin Email:", anchor="w", bg='white')
    admin_email_label.pack(pady=5)
    make_label_transparent(admin_email_label)
    admin_email_entry = tk.Entry(admin_login_box)
    admin_email_entry.pack(pady=5, ipadx=10)  # Adjust ipadx for entry width

    admin_password_label = tk.Label(admin_login_box, text="Admin Password:", anchor="w", bg='white')
    admin_password_label.pack(pady=5)
    make_label_transparent(admin_password_label)
    admin_password_entry = tk.Entry(admin_login_box, show="*")
    admin_password_entry.pack(pady=5, ipadx=10)  # Adjust ipadx for entry width

    admin_login_button = tk.Button(admin_login_box, text="Login", bg='yellowgreen', command=admin_accounts, font=("Arial", 12))
    admin_login_button.pack(pady=10)

    def back_to_main():
        admin_login_box.destroy()
        root.deiconify()

    # Button to go back to the home page
    back_button = tk.Button(admin_login_box, text="Close", command=back_to_main, bg="gray", font=("Arial", 12))
    back_button.pack(pady=10)

    
    admin_login_box.mainloop()

    
def delete_appointment(appointmentid, cursor, connection):
    try:
        if connection:
            query = f"DELETE FROM appointments WHERE Appointment_IdNo = {appointmentid}"
            cursor.execute(query)
            connection.commit()
            messagebox.showinfo("Success", "Appointment deleted successfully!")
        else:
            messagebox.showerror("Error", "Database connection is not valid.")
    except Exception as e:
        messagebox.showerror("Error", f"Error deleting appointment: {str(e)}")


def create_admin_window(cursor, mydb):
    global admin_window
    admin_window = tk.Toplevel(root)
    admin_window.title("Admin Window")
    admin_window.geometry("1360x750")
    
    # Create a frame for displaying appointments
    admin_frame = tk.Frame(admin_window, borderwidth=2, relief="ridge", padx=10, pady=10)
    admin_frame.pack(expand=True, fill="both")

    # Add a label to display appointments
    appointments_label = tk.Label(admin_frame, text="Appointments", font=("Times", "16", "bold"))
    appointments_label.grid(row=0, column=0, columnspan=7, pady=(0, 10))

    # Create Treeview widget for displaying appointments
    tree = ttk.Treeview(admin_frame, columns=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11), show="headings", height=20)
    tree.grid(row=1, column=0, columnspan=7, pady=(0, 10), padx=10)

    # Set column headings
    tree.heading(1, text="ID")
    tree.heading(2, text="Name")
    tree.heading(3, text="Age")
    tree.heading(4, text="Contact")
    tree.heading(5, text="Sex")
    tree.heading(6, text="Reason")
    tree.heading(7, text="Doctor")
    tree.heading(8, text="Time")
    tree.heading(9, text="Date")
    tree.heading(10, text="Amount")
    tree.heading(11, text="Disease")

    # Set column widths
    tree.column(1, width=40)  
    tree.column(2, width=150)  
    tree.column(3, width=40)   
    tree.column(4, width=150)   
    tree.column(5, width=150)  
    tree.column(6, width=120)  
    tree.column(7, width=120)  
    tree.column(8, width=150)  
    tree.column(9, width=150) 
    tree.column(10, width=100) 
    tree.column(11, width=150)
    
    # Add alternating row colors
    tree.tag_configure('oddrow', background='#E8E8E8')
    tree.tag_configure('evenrow', background='#FFFFFF')

    # Query the database to retrieve appointment information
    query = "SELECT * FROM appointments"
    cursor.execute(query)
    appointments = cursor.fetchall()

    # Insert appointment information into the Treeview widget
    for idx, appointment in enumerate(appointments, start=1):
        tags = ('evenrow', 'oddrow')[idx % 2]
        tree.insert("", "end", values=appointment, tags=tags)

    def delete_selected_appointment():
        selected_item = tree.selection()
        if selected_item:
            appointment_id = tree.item(selected_item, "values")[0]
            confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this appointment?")
            if confirm:
                delete_appointment(appointment_id, cursor, mydb)
                refresh_appointments()
        else:
            messagebox.showerror("Error", "Please select an appointment to delete")

    # Add a button to delete selected appointment
    delete_button = tk.Button(admin_frame, text="Delete Appointment", command=delete_selected_appointment, bg="red", fg="white", relief="raised", font=("Helvetica", 12), width=15)
    delete_button.grid(row=2, column=0, pady=(10, 0), padx=5)

    # Refresh appointments function
    def refresh_appointments():
        # Clear existing items in the Treeview
        for item in tree.get_children():
            tree.delete(item)

        # Query the database to retrieve updated appointment information
        cursor.execute(query)
        appointments = cursor.fetchall()

        # Insert updated appointment information into the Treeview widget
        for idx, appointment in enumerate(appointments, start=1):
            tags = ('evenrow', 'oddrow')[idx % 2]
            tree.insert("", "end", values=appointment, tags=tags)

    # Optionally, you can add a refresh button
    refresh_button = tk.Button(admin_frame, text="Refresh Appointments", command=refresh_appointments, bg="lightgreen", relief="raised", font=("Helvetica", 12), width=19)
    refresh_button.grid(row=2, column=1, pady=(10, 0), padx=5)

    def create_search_window():
        global search_results_tree  # Declare search_results_tree as global
        admin_window.destroy()

        def back_to_admin_window():
            search_window.destroy()  # Close the search window
            create_admin_window(cursor, mydb)  # Call the function to create the admin window

                
        search_window = tk.Toplevel(root)
        search_window.title("Search Appointments")
        search_window.geometry("1360x600")

        # Create a frame for the search window
        search_frame = tk.Frame(search_window, borderwidth=2, relief="ridge", padx=10, pady=20)
        search_frame.pack(expand=True, fill="both")

        # Search Label and Entry
        search_label = tk.Label(search_frame, text="Search Appointments", font=("Arial", 18, "bold"))
        search_label.grid(row=0, column=0, columnspan=2, pady=(20, 10))

        global search_entry  # Declare search_entry as global
        search_entry = tk.Entry(search_frame, width=40, font=("Arial", 14))
        search_entry.grid(row=1, column=0, padx=10, pady=10, sticky="e")

        def resize_image(image_path, width, height):
            original_image = Image.open(image_path)
            resized_image = original_image.resize((width, height), Image.Resampling.NEAREST)
            photo = ImageTk.PhotoImage(resized_image)
            return photo

        search_logo_path = "D:/Nykhole's Files - Copy/[ALL] BSU - SECOND YEAR/FILES/ADV. COMPROG/HMS_DB/search.png"
        resized_search_logo = resize_image(search_logo_path, 20, 20)

        search_button = tk.Button(search_frame, command=search_appointments,
                                image=resized_search_logo, bg="#4CAF50",
                                fg="white", relief="raised", font=("Arial", 14), width=40)
        search_button.image = resized_search_logo
        search_button.grid(row=1, column=1, padx=0, pady=10, sticky="w")

        global search_results_tree  # Declare search_results_tree as global
        search_results_tree = ttk.Treeview(search_frame, columns=("Name", "Date", "Time", "Doctor", "Reason", "Disease"),
                                        show="headings", height=15)
        search_results_tree.heading("#1", text="Name")
        search_results_tree.heading("#2", text="Date")
        search_results_tree.heading("#3", text="Time")
        search_results_tree.heading("#4", text="Doctor")
        search_results_tree.heading("#5", text="Reason")
        search_results_tree.heading("#6", text="Disease")

        search_results_tree.grid(row=2, column=0, columnspan=2, padx=10, pady=(20, 10), sticky="nsew")
        
        # Set column widths
        for i in range(1, 5):
            search_results_tree.column(i, width=150)

        # Add alternating row colors
        search_results_tree.tag_configure('oddrow', background='#E8E8E8')
        search_results_tree.tag_configure('evenrow', background='#FFFFFF')

        # Scrollbars
        scrollbar_x = ttk.Scrollbar(search_frame, orient="horizontal", command=search_results_tree.xview)
        scrollbar_x.grid(row=3, column=0, columnspan=2, sticky="ew")
        search_results_tree.configure(xscrollcommand=scrollbar_x.set)

        scrollbar_y = ttk.Scrollbar(search_frame, orient="vertical", command=search_results_tree.yview)
        scrollbar_y.grid(row=2, column=2, sticky="ns")
        search_results_tree.configure(yscrollcommand=scrollbar_y.set)

        # Configure row and column weights
        search_frame.grid_rowconfigure(2, weight=1)
        search_frame.grid_columnconfigure(0, weight=1)

        # Back Button
        back_button_path = "D:/Nykhole's Files - Copy/[ALL] BSU - SECOND YEAR/FILES/ADV. COMPROG/HMS_DB/back.png"  # Provide the path to your back button image
        resized_back_button = resize_image(back_button_path, 30, 30)  # Adjust the size as needed
  
        back_button = tk.Button(search_frame, image=resized_back_button, bg="gray", command=back_to_admin_window)
        back_button.image = resized_back_button  # Keep a reference to the image to prevent garbage collection
        back_button.grid(row=0, column=1, pady=(20, 10), padx=10, sticky="e")

       
        search_window.protocol("WM_DELETE_WINDOW", search_window.destroy)
        search_window.mainloop()


    # Search button
    search_button = tk.Button(admin_frame, text="Search Appointments", command=create_search_window, bg="lightblue", relief="raised", font=("Helvetica", 12), width=20)
    search_button.grid(row=2, column=2, pady=(10, 0), padx=5)
    
    def admin_logout():
        global admin_logged_in
        admin_logged_in = False
        messagebox.showinfo("Admin Log Out", "Admin logged out successfully!")
        admin_window.destroy()
        root.deiconify()

    # Logout button with improved styling
    logout_button = tk.Button(admin_frame, text="Log Out", command=admin_logout, bg="lightcoral", relief="raised", font=("Helvetica", 12), width=15)
    logout_button.grid(row=2, column=3, pady=(10, 0), padx=5)

    
    admin_window.mainloop()


def login():
    global email_entry, password_entry, full_name_entry
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
                login_window.destroy()
                open_appointment_window(full_name, age, sex)
            else:
                messagebox.showerror("Login Failed", "Invalid email or password")
        else:
            messagebox.showerror("Login Failed", "Invalid email or password")
    else:
        messagebox.showerror("Invalid Information", "Please fill in both email and password.")

def remove_signup():
        signup_box.destroy()
        root.deiconify()

def signup():
    global full_name, age, sex, full_name_entry
    full_name = full_name_entry.get()
    age = age_entry.get()
    sex = sex_var.get()
    email = email_entry.get()
    password = password_entry.get()
    if  "@gmail.com" not in email:
        messagebox.showerror("Invalid Email", "Please enter a valid Gmail address.")
        return
    if full_name and age and sex and email and password:
        if insert_users_into_db(full_name, age, sex, email, password):
            messagebox.showinfo("Signup Successful", "Account created successfully!")
            remove_signup()
            open_appointment_window(full_name, age, sex)
        else:
            messagebox.showerror("Signup Failed", "Failed to create an account. Please try again.")
    else:
        messagebox.showerror("Invalid Information", "Please fill in all the information needed.")


# Initialize the admin login state


admin_logged_in = False


def admin_accounts():
    global admin_window
    global admin_logged_in
    admin_credentials = {
        "dra.dalusung@gmail.com": "admin01",
        "dra.festejo@gmail.com": "admin02",
        "dra.isip@gmail.com": "admin03",
        "dr.sutare@gmail.com": "admin04",
        "admin":"admin"
    }

    entered_email = admin_email_entry.get()
    entered_password = admin_password_entry.get()

    if entered_email in admin_credentials and entered_password == admin_credentials[entered_email]:
        admin_logged_in = True
        admin_window()
        admin_login_box.destroy()
    else:
        messagebox.showerror("Admin Login Failed", "Invalid email or password")

# Function to create the admin window

cursor = mydb.cursor()
def admin_window():
    admin_login_box.destroy()
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

# Create a separate function to hide the main window
def hide_main_window():
    root.withdraw()

# Create a separate function to destroy the main window
def destroy_main_window():
    root.destroy()

# Create a function to show the homepage
def show_homepage():
    destroy_main_window()


def hms_info():
    # Hide the main window
    root.iconify()

    # Create a new window for displaying HMS information
    info_window = tk.Tk()
    info_window.geometry("1360x720")
    info_window.title("About HMS")

    # Create a Canvas with a solid color background
    canvas = tk.Canvas(info_window, width=1110, height=50, bg="lightgray")
    canvas.pack()

    # Add a border to the Canvas to simulate an image
    border = tk.Frame(info_window, bd=10, relief="ridge", bg="white")
    border.place(relx=0, rely=0, relwidth=1, relheight=1)

    # Add labels or other widgets to provide information about HMS
    info_label = tk.Label(border, text="TCNR's HOSPITAL MANAGEMENT SYSTEM", font=("Arial", 20, "bold"), bg="white", fg="black")
    info_label.pack(pady=8)

    # Create frames for doctors, credibility, and additional info with custom size
    doctors_frame = create_doctors_frame(info_window)
    tcnr_info_frame = create_tcnr_info_frame(info_window)

    # Function to switch to the doctors frame
    def show_doctors_info():
        doctors_frame.pack(fill="both", expand=True)
        tcnr_info_frame.pack_forget()

    # Function to switch to TCNR's Information frame
    def show_tcnr_info():
        doctors_frame.pack_forget()
        tcnr_info_frame.pack(fill="both", expand=True)

    # Button to show doctors
    show_doctors_button = tk.Button(info_window, text="Show Doctors Information", command=show_doctors_info, bg="lightblue", fg="black")
    show_doctors_button.pack(side="left", anchor="ne", padx=10, pady=10)

    # Button to show TCNR's Information
    show_tcnr_info_button = tk.Button(info_window, text="TCNR's Details", command=show_tcnr_info, bg="lightblue", fg="black")
    show_tcnr_info_button.pack(side="left", anchor="ne", padx=10, pady=10)

    # Add a button to close the info window and show the main window
    close_button = tk.Button(info_window, text="Close", command=lambda: show_main_window_from_info(info_window), bg="gray", fg="white")
    close_button.pack(side="right", anchor="ne", padx=10, pady=10)

    info_window.mainloop()


def create_doctors_frame(parent):
    frame = tk.Frame(parent, bg="#f4f4f4")

    # Header with background color
    header_frame = tk.Frame(frame, bg="#3498db")  # Use your preferred color
    header_frame.pack(fill="x", padx=5, pady=5)

    doctors_label = tk.Label(header_frame, text="Doctors Information", font=("Arial", 20,), bg="#3498db", fg="white")  # Adjust text color
    doctors_label.pack(pady=10)

    # Create a Treeview widget for displaying the table with styling
    tree = ttk.Treeview(frame, columns=("Name", "Age", "Sex", "Birthday", "Language Used", "Citizenship", "Religion", "Education", "Contact"), show="headings", selectmode="browse")

    # Set column headings
    tree.heading("Name", text="Name")
    tree.heading("Age", text="Age")
    tree.heading("Sex", text="Sex")
    tree.heading("Birthday", text="Birthday")
    tree.heading("Language Used", text="Language Used")
    tree.heading("Citizenship", text="Citizenship")
    tree.heading("Religion", text="Religion")
    tree.heading("Education", text="Education")
    tree.heading("Contact", text="Contact")

    # Set column widths
    column_widths = [200, 40, 60, 110, 105, 80, 100, 200, 110]
    for i, width in enumerate(column_widths):
        tree.column(tree['columns'][i], width=width)

    # Style the Treeview
    style = ttk.Style()
    style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#3498db", foreground="white")  # Adjust background and foreground colors
    style.configure("Treeview", font=("Arial", 12), rowheight=25)

    # Sample data (replace this with actual data)
    data = [("Dra. Trisha Marie Dalusung, PhD ", 30, "Female", "August-08-1993", "English, Tagalog", "Filipino", "Roman Catholic", "Master's Degree in Psychology", "09393027628"),
            ("Dra. Chloie Ysabelle Festejo, MMLT ", 29, "Female", "March-30-1994", "English, Tagalog", "Filipino", "Roman Catholic", "Master in Medical Lab Technology", "09764129948"),
            ("Dra. Nykhole Isip, MD", 30, "Female", "May-21-1993", "English, Tagalog", "Filipino", "Roman Catholic", "Doctor of Osteopathic Medicine", "09916910478"),
            ("Dr. Rey Aldrin Sutare, MSc ", 29, "Male", "January-17-1994", "English, Tagalog", "Filipino", "Roman Catholic", "Master of Science in Optometry", "09108020365")
            ]

    # Alternate row colors for better readability
    for i, row in enumerate(data):
        tag = "even" if i % 2 == 0 else "odd"
        tree.insert("", "end", values=row, tags=(tag,))

    tree.tag_configure("even", background="#ecf0f1")  # Use your preferred color for even rows
    tree.tag_configure("odd", background="white")  # Use your preferred color for odd rows

    # Create a vertical scrollbar
    v_scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    v_scrollbar.pack(side="right", fill="y")

    # Create a horizontal scrollbar
    h_scrollbar = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    h_scrollbar.pack(side="bottom", fill="x")

    # Configure the Treeview to use both vertical and horizontal scrollbars
    tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

    # Set the mousewheel event for zooming
    def on_mousewheel(event):
        if event.delta:
            scale = 1.001 ** (event.delta // 120)
            new_size = int(tree.cget("font").split()[1]) * scale
            tree.configure(font=("Arial", int(new_size)))

    # Bind the mousewheel event to the tree
    tree.bind("<MouseWheel>", on_mousewheel)

    # Pack the Treeview
    tree.pack(fill="both", expand=True)

    return frame

def create_tcnr_info_frame(parent):
    frame = tk.Frame(parent, bg="#f4f4f4")  # Light gray background

    # Header with background color
    header_frame = tk.Frame(frame, bg="#27ae60")  # Green header
    header_frame.pack(fill="x", padx=5, pady=5)

    tcnr_info_label = tk.Label(header_frame, text="TCNR's Hospital Information", font=("Arial", 20), bg="#27ae60", fg="white")  # Adjust text color
    tcnr_info_label.pack(pady=10)

    # Add labels with TCNR's information
    labels = [
        ("Hospital Name", "TCNR's Hospital"),
        ("Location", "Alangilan, Batangas City, Batangas, Philippines"),
        ("Established", "2023"),
        ("Founder", "CICS Inc."),
        ("Services", "Good Health and Well-being"),
        ("About", '''TCNR's Hospital Management System (HMS) is crucial for streamlined information management in healthcare. It efficiently handles patient records, appointments, and billing, ensuring accuracy and accessibility. This improves coordination among healthcare providers, leading to enhanced patient care. Real-time data access empowers decision-making for effective resource allocation. The system integrates robust security measures to protect sensitive patient information, addressing data privacy concerns.''')
        # Add more information as needed
    ]

    for label in labels:
        label_frame = tk.Frame(frame, bg="#f4f4f4")  # Light gray background for each label
        label_frame.pack(fill="x", pady=(5, 0))

        label_text = tk.Label(label_frame, text=f"{label[0]}:", font=("Arial", 12, "bold"), bg="#f4f4f4", fg="#2c3e50")  # Dark gray text
        label_text.pack(pady=5, anchor="w")

        if label[0] == "About":
            # Single label for the "About" section without visual separation
            value_text = tk.Label(frame, text=label[1], font=("Arial", 10), bg="#f4f4f4", fg="#333333", wraplength=600, justify="left")  # Dark gray text
            value_text.pack(pady=(0, 10), anchor="w")
        else:
            value_text = tk.Label(label_frame, text=label[1], font=("Arial", 10), bg="#f4f4f4", fg="#333333", wraplength=600, justify="left")  # Dark gray text
            value_text.pack(pady=(0, 10), anchor="w")

    return frame

def show_main_window_from_info(info_window):
    # Show the main window again
    root.deiconify()

    # Destroy the info window
    info_window.destroy()


# Dictionary to store appointments
appointments = {}


def open_appointment_window(full_name, age, sex):
    global appointment_window  # Declare the appointment_window as global
    global appointments  # Declare appointments as global
    global date_entry
    global full_name_entry
    appointment_window = tk.Toplevel(root)
    appointment_window.geometry("500x700")
    appointment_window.title("Appointment Scheduling")

    background_image = Image.open("D:/Nykhole's Files - Copy/[ALL] BSU - SECOND YEAR/FILES/ADV. COMPROG/HMS_DB/signup.png")
    background_image = background_image.resize((500,700), Image.Resampling.NEAREST)
    background_photo = ImageTk.PhotoImage(background_image)

    background_label = tk.Label(appointment_window, image=background_photo)
    background_label.place(x=0, y=0, relwidth=1, relheight=1)

    # Keep a reference to the image to prevent garbage collection   
    background_label.image = background_photo


    # Create an appointment frame within the appointment window
    appointment_frame = tk.Frame(appointment_window, borderwidth=2, relief="ridge", padx=10, pady=10)
    appointment_frame.pack(padx=20, pady=20)

    cursor = mydb.cursor()

    # Hide the main window
    root.withdraw()


    def schedule_appointment():
        global appointments
        global date_entry
        global full_name_entry

        patient_name = full_name_entry.get()
        patient_age = age_entry.get()
        contact_number = contact_entry.get()
        sex = sex_entry.get()
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


    # Create an entry widget for full_name
    full_name_label = tk.Label(appointment_window, text="Full Name:")
    full_name_label.pack()
    full_name_entry = tk.Entry(appointment_window)
    full_name_entry.pack()
    full_name_entry.insert(0, full_name)
    full_name_label.pack_forget()
    full_name_entry.pack_forget()

    age_label = tk.Label(appointment_window, text="Age:")
    age_label.pack()
    age_entry = tk.Entry(appointment_window)
    age_entry.pack()
    age_entry.insert(0, age)
    age_label.pack_forget()
    age_entry.pack_forget()

    sex_label = tk.Label(appointment_window, text="Sex:")
    sex_label.pack()
    sex_entry = tk.Entry(appointment_window)
    sex_entry.pack()
    sex_entry.insert(0, sex)
    sex_label.pack_forget()
    sex_entry.pack_forget()

    contact_label = tk.Label(appointment_window, text="Contact Number:", bg="white")
    contact_label.pack(pady=3)

    def validate_phone_number(input_text):
        if input_text.isdigit() or input_text == "":
            return True
        else:
            messagebox.showerror("Invalid Phone Number", "Please enter only numeric values for the phone number.")
            return False

    validate_phone_number_cmd = appointment_window.register(validate_phone_number)
    contact_entry = tk.Entry(appointment_window, validate="key", validatecommand=(validate_phone_number_cmd, "%P"))
    contact_entry.pack(pady=3)

    reasons_label = tk.Label(appointment_window, text="Reason of Appointment:", bg="white")
    reasons_label.pack(pady=3)
    reasons_var = tk.StringVar()
    reasons_var.set("Checkup")
    reasons_radio_checkup = tk.Radiobutton(appointment_window, text="Checkup", variable=reasons_var, value="Checkup", bg="white")
    reasons_radio_medication = tk.Radiobutton(appointment_window, text="Medication", variable=reasons_var, value="Medication", bg="white")
    reasons_radio_checkup.pack(pady=3)
    reasons_radio_medication.pack(pady=3)

    disease_label = tk.Label(appointment_window, text="Patient's Disease:", bg="white")
    disease_label.pack(pady=3)
    disease_entry = tk.Entry(appointment_window)
    disease_entry.pack(pady=3)


    # Create a dictionary to store doctors and their available slots
    doctors = {
        "Dra. Dalusung, PhD": ["9:00 AM - 10:00 AM", "2:00 PM - 3:00 PM"],
        "Dra. Festejo, MMLT": ["10:00 AM - 11:00 AM", "3:00 PM - 4:00 PM"],
        "Dra. Isip, MD": ["7:00 AM - 8:00 AM", "5:00 PM - 6:00 PM"],
        "Dr. Sutare, MSc": ["11:00 AM - 12:00 PM", "7:00 PM - 8:00 PM"],
        }

    doctor_label = tk.Label(appointment_window, text="Select Doctor:", bg="white")
    doctor_label.pack(pady=3)
    doctor_var = tk.StringVar(value=list(doctors.keys())[0])  # Set the default doctor
    doctor_option_menu = tk.OptionMenu(appointment_window, doctor_var, *doctors.keys())
    doctor_option_menu.pack(pady=3)


    def update_slot_options(*args):
        selected_doctor = doctor_var.get()
        # Update the slots when the doctor changes
        slot_option_menu['menu'].delete(0, 'end')  # Clear the current slots
        for slot in doctors[selected_doctor]:
            slot_option_menu['menu'].add_command(label=slot, command=tk._setit(slot_var, slot))

    doctor_var.trace("w", update_slot_options)  # Update slots when the doctor changes

    slot_label = tk.Label(appointment_window, text="Select Slot:", bg="white")
    slot_label.pack(pady=3)
    slot_var = tk.StringVar(value=doctors[doctor_var.get()][0])  # Set the default slot
    slot_option_menu = tk.OptionMenu(appointment_window, slot_var, *doctors[doctor_var.get()])
    slot_option_menu.pack(pady=3)

    date_label = tk.Label(appointment_window, text="Appointment Date:", bg="white")
    date_label.pack(pady=3)
    date_entry = Calendar(appointment_window, selectmode="day", year=2023, month=1, day=1)
    date_entry.pack(pady=3)

    schedule_button = tk.Button(appointment_window, text="Schedule Appointment", command=schedule_appointment, bg="green", fg="white", font=("Arial", 12))
    schedule_button.pack(pady=5)

    def back_to_main():
        appointment_window.destroy()
        root.deiconify()

    back_button = tk.Button(appointment_window, text="Close", command=back_to_main, bg="gray", font=("Arial", 12))
    back_button.pack(pady=10)

    # Make sure to destroy the appointment frame properly when it's closed
    appointment_window.protocol("WM_DELETE_WINDOW", close_appointment_window)
    appointment_window.mainloop()

    root.withdraw()

def show_main_window():
    root.deiconify()

def close_appointment_window():
    appointment_window.destroy()
    show_main_window()

summary_window = None

def show_appointment_summary(appointment_info):
    global summary_window

    # Check if the selected slot is still available
    selected_doctor = appointment_info.get("Doctor", "")
    selected_slot = appointment_info.get("Appointment Time", "")
    selected_doctor_slots = doctors.get(selected_doctor, [])

    if selected_doctor_slots and selected_slot not in selected_doctor_slots:
        messagebox.showerror("Doctor Slot Full", "The selected doctor's slot is already full. Please choose another slot.")
        return

    close_appointment_window()

    # Hide the main window
    root.withdraw()

    # Check if the summary_window is already open, and close it if it is
    if summary_window:
        summary_window.destroy()

    def update_appointment():
        root.iconify
        global update_window
        global summary_window
        update_window = tk.Toplevel(root)
        update_window.geometry("500x650")
        update_window.title("Update Appointment")

        # Create entry widgets for each field to allow editing
        updated_info = {}
        for index, (key, value) in enumerate(appointment_info.items(), start=1):
            label = tk.Label(update_window, text=f"{key}:", font=("Arial", 12))
            label.grid(row=index, column=0, pady=5, padx=10, sticky="w")

            entry = tk.Entry(update_window, font=("Arial", 12))

            if key == "Amount":
                entry.insert(0, value)
                entry.configure(state="disabled")  # Disable the entry for Amount
            else:
                entry.insert(0, value)

            entry.grid(row=index, column=1, pady=5, padx=10, sticky="e")
            updated_info[key] = entry

        # Function to update the appointment in the database
        def save_updated_appointment():
            update_values = {key: entry.get() if hasattr(entry, 'get') else entry for key, entry in updated_info.items()}

            try:
                update_values["Age"] = int(update_values["Age"])
                update_values["Contact Number"] = int(update_values["Contact Number"])
            except ValueError:
                messagebox.showerror("Error", "Please enter valid integer values for Age and Contact Number.")
                return

            # Check the selected reason and update the amount accordingly
            selected_reason = update_values.get("Reason", "")
            if selected_reason == "Checkup":
                update_values["Amount"] = "500 pesos"
            elif selected_reason == "Medication":
                update_values["Amount"] = "1,200 pesos"

            # Update the database with the modified information
            update_query = """
                UPDATE appointments 
                SET Patient_Name=%(Name)s, 
                    Age=%(Age)s, 
                    Contact_Number=%(Contact Number)s, 
                    Sex=%(Sex)s, 
                    Reason=%(Reason)s, 
                    Disease=%(Disease)s, 
                    Doctor=%(Doctor)s, 
                    Appointment_Time=%(Appointment Time)s, 
                    Appointment_Date=%(Appointment Date)s, 
                    Amount=%(Amount)s 
                WHERE Patient_Name=%(Name)s and Contact_Number=%(Contact Number)s
            """

            # Convert values to appropriate data types
            update_values = {
                "Name": str(update_values["Name"]),  
                "Age": int(update_values["Age"]),    
                "Contact Number": int(update_values["Contact Number"]),
                "Sex": str(update_values["Sex"]),    
                "Reason": str(update_values["Reason"]),
                "Disease": str(update_values["Disease"]), 
                "Doctor": str(update_values["Doctor"]),  
                "Appointment Time": str(update_values["Appointment Time"]),  
                "Appointment Date": str(update_values["Appointment Date"]),  
                "Amount": str(update_values["Amount"]),  
            }

            print("Update Query:", update_query)
            print("Update Values:", update_values)

            try:
                cursor.execute(update_query, update_values)
                mydb.commit()
                messagebox.showinfo("Update Successful", "Appointment updated successfully!")

                # Close the current update window
                update_window.destroy()

                # Recreate the appointment summary window with the updated information
                show_appointment_summary(update_values)

            except mysql.connector.Error as e:
                print("Error while updating the database:", str(e))
                mydb.rollback()
                messagebox.showerror("Error", "Failed to update the appointment. Please try again.")

        save_updated_appointment_button = tk.Button(update_window, text="Save Updated Appointment", command=save_updated_appointment, bg="green", fg="white", font=("Arial", 12))
        save_updated_appointment_button.grid(row=len(updated_info) + 1, column=1, pady=10)

    # Create the new summary window
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
    update_appointment_button = tk.Button(summary_window, text="Update Appointment", command=update_appointment, bg="#4CAF50", fg="white", font=("Arial", 12))
    update_appointment_button.grid(row=len(appointment_info) + 1, column=0, pady=10, padx=10, sticky="w")

    # Create a button to print and save the summary
    print_summary_button = tk.Button(summary_window, text="Print Summary and Save to File", command=lambda: save_summary_to_file(appointment_info), bg="#4285f4", fg="white", font=("Arial", 12))
    print_summary_button.grid(row=len(appointment_info) + 1, column=1, pady=10, padx=10, sticky="w")

    # Create a "Cancel Appointment" button
    cancel_button = tk.Button(summary_window, text="Cancel Appointment", command=lambda: cancel_appointment(appointment_info), bg="#f44336", fg="white", font=("Arial", 12))
    cancel_button.grid(row=len(appointment_info) + 2, column=0, pady=10, padx=10, sticky="w")

    def back_to_main():
        # Close the summary window
        summary_window.destroy()
        # Show the main window again
        root.deiconify()

    # Create a "Close System" button
    close_system_button = tk.Button(summary_window, text="Close", command=back_to_main, bg="gray", fg="white", font=("Arial", 12))
    close_system_button.grid(row=len(appointment_info) + 2, column=1, pady=10, padx=10, sticky="w")

    # Display the summary window
    summary_window.mainloop()

# Function to show the main window
def show_main_window():
    root.deiconify()

# Add this function to handle appointment cancellation
def cancel_appointment(appointment_info):
    result = messagebox.askquestion("Cancel Appointment", "Are you sure you want to cancel this appointment?")
    if result == "yes":
        # Retrieve the patient's name and contact number from the appointment_info dictionary
        patient_name = appointment_info.get("Name")
        contact_number = appointment_info.get("Contact Number")

        if patient_name is not None and contact_number is not None:
            # Delete the appointment from the database
            delete_query = "DELETE FROM appointments WHERE Patient_Name=%s AND Contact_Number=%s"
            delete_values = (patient_name, contact_number)

            try:
                cursor.execute(delete_query, delete_values)
                mydb.commit()
                messagebox.showinfo("Appointment Canceled", "The appointment has been cancelled.")
                summary_window.destroy()
                root.deiconify()
            except mysql.connector.Error as e:
                print("Error while canceling the appointment:", str(e))
                mydb.rollback()
                messagebox.showerror("Error", "Failed to cancel the appointment. Please try again.")
        else:
            messagebox.showerror("Error", "Unable to retrieve appointment information.")


# Create a dictionary to store doctors and their available slots
doctors = {
    "Dra. Dalusung, PhD": ["9:00 AM - 10:00 AM", "2:00 PM - 3:00 PM"],
    "Dra. Festejo, MMLT": ["10:00 AM - 11:00 AM", "3:00 PM - 4:00 PM"],
    "Dra. Isip, MD": ["7:00 AM - 8:00 AM", "5:00 PM - 6:00 PM"],
    "Dr. Sutare, MSc": ["11:00 AM - 12:00 PM", "7:00 PM - 8:00 PM"],
}
def stop_system():
    root.destroy()

# Modify the search_appointments function to search all attributes
def search_appointments():
    global search_entry
    search_term = search_entry.get()

    try:
        query = "SELECT * FROM appointments WHERE "
        params = []  # Create a list to store the search parameters

        if search_term:
            query += (
                "LOWER(patient_name) LIKE LOWER(%s) OR "
                "LOWER(appointment_date) LIKE LOWER(%s) OR "
                "LOWER(appointment_time) LIKE LOWER(%s) OR "
                "LOWER(doctor) LIKE LOWER(%s) OR "
                "LOWER(reason) LIKE LOWER(%s) OR "
                "LOWER(disease) LIKE LOWER(%s)"
            )
            params.extend([f"%{search_term}%"] * 6)

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
        search_results_tree.insert("", "end", values=(result[1], result[8], result[7], result[6], result[5], result[10]))

class AppointmentPDF(FPDF):
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
    """
    Save appointment summary to a PDF file.

    Args:
        appointment_info (dict): Dictionary containing appointment information.
    """
    try:
        # Open a file dialog to choose the save location and filename
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Appointment Summary As"
        )

        if file_path:
            pdf = AppointmentPDF()
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

def close_main_window():
    # Close the main window
    root.destroy()

# Create the main window
root = tk.Tk()
root.geometry("1360x760")
root.title("Hospital Management System")

# Load and display the background image
background_image = Image.open("D:/Nykhole's Files - Copy/[ALL] BSU - SECOND YEAR/FILES/ADV. COMPROG/HMS_DB/TCNR.png")
background_image = background_image.resize((1360,760), Image.Resampling.NEAREST)
background_photo = ImageTk.PhotoImage(background_image)

background_label = tk.Label(root, image=background_photo)
background_label.place(x=0, y=0, relwidth=1, relheight=1)


def display_homepage():
    # Create a frame for the buttons
    button_frame = tk.Frame(root, bg="lightblue")
    button_frame.place(relx=1, rely=0, anchor="ne")  # Adjust relx, rely, and anchor

    # Create buttons for admin login, regular login, sign up, HMS info, and system close
    close_system_button = tk.Button(button_frame, text="Close System", command=root.destroy, bg="#FF0000", fg="white", width=15)
    close_system_button.pack(side="right", padx=10, pady=10)

    admin_login_button = tk.Button(button_frame, text="Admin Login", command=create_admin_login_box, bg="#0000FF", fg="white", width=15)
    admin_login_button.pack(side="right", padx=10, pady=10)

    user_login_button = tk.Button(button_frame, text="User Login", command=create_login_box, bg="#228B22", fg="white", width=15)
    user_login_button.pack(side="right", padx=10, pady=10)

    signup_button = tk.Button(button_frame, text="Sign Up", command=create_signup_box, bg="#228B22", fg="white", width=15)
    signup_button.pack(side="right", padx=10, pady=10)

    hms_info_button = tk.Button(button_frame, text="About HMS", command=hms_info, bg="#800080", fg="white", width=15)
    hms_info_button.pack(side="right", padx=10, pady=10)

# Initialize the main window with homepage content
display_homepage()


root.mainloop()
mydb.close()