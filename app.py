from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_wtf import FlaskForm 
import bcrypt
import os
import MySQLdb.cursors
from wtforms import StringField, PasswordField,SubmitField
from wtforms.validators import DataRequired, Email , ValidationError
from flask_mysqldb import MySQL
from functools import wraps
import pandas as pd

app = Flask(__name__)

# MYSQL
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '8010'
app.config['MYSQL_DB'] = 'dairy_db'
app.secret_key = "jdsfidbgiunjnrog65464svz85"
mysql = MySQL(app)

class RegisterForm(FlaskForm):
    First_name = StringField("First_Name",validators=[DataRequired()])
    Last_name = StringField("Last_Name",validators=[DataRequired()])
    Mobile = StringField("Mobile",validators=[DataRequired()])
    Email = StringField("Email",validators=[DataRequired(),Email()])
    Password= StringField("Password",validators=[DataRequired()])
    Submit = SubmitField("signup")

class LoginForm(FlaskForm):
    Email = StringField("Email",validators=[DataRequired(),Email()])
    Password= StringField("Password",validators=[DataRequired()])
    Submit = SubmitField("Login")
 

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:  # Check if the user is logged in
        session.pop("user_id", None)  # Log out the user
        flash("You have been logged out as you revisited the login page.")
        return redirect(url_for("login"))  # Redirect to login again to display the form
    
    form = LoginForm()
    if form.validate_on_submit():
        Email = form.Email.data
        Password = form.Password.data

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM user WHERE email = %s", (Email,))
        user = cursor.fetchone()
        cursor.close()

        if user:
            if bcrypt.checkpw(Password.encode('utf-8'), user[4].encode('utf-8')):
                session['user_id'] = user[3]  # Store email in session
                return redirect(url_for("dashboard"))
            else:
                flash("Incorrect password.")
        else:
            flash("No user found with that email.")
    return render_template("login.html", form=form)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "user_id" in session:  # Check if the user is logged in
        session.pop("user_id", None)  # Log out the user
        flash("You have been logged out as you revisited the signup page.")
        return redirect(url_for("signup"))  # Redirect to signup again to display the form

    form = RegisterForm()
    if form.validate_on_submit():
        First_name = form.First_name.data
        Mobile = form.Mobile.data
        Last_name = form.Last_name.data
        Email = form.Email.data
        Password = form.Password.data
        hashedpw = bcrypt.hashpw(Password.encode('utf-8'), bcrypt.gensalt())
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO user (First_name, Last_name, Mobile, Email, Password) VALUES (%s, %s, %s, %s, %s)", 
                       (First_name, Last_name, Mobile, Email, hashedpw))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for("login"))
    return render_template("signup.html", form=form)


@app.route("/dashboard")
@login_required
def dashboard():
    if "user_id" in session:
        email = session["user_id"]  # Get the email from the session
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            # Fetch user details
            cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
            user = cursor.fetchone()

            # Fetch total milk collected for the current date
            query = """
                SELECT SUM(milk) AS total_milk_collected 
                FROM milk_collection 
                WHERE DATE(collection_time) = CURRENT_DATE AND email = %s
            """
            cursor.execute(query, (email,))
            result = cursor.fetchone()

            # Calculate total milk
            total_milk = result['total_milk_collected'] if result['total_milk_collected'] else 0
            total_milk = round(total_milk, 2)

        except Exception as e:
            flash(f"Error: {e}", "danger")
            user = None
            total_milk = 0
        finally:
            if cursor:
                cursor.close()

        if user:
            return render_template('dashboard.html', user=user, total_milk=total_milk)

    return redirect(url_for("login"))


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    flash("you have been logged out succesfully")  # Remove the user ID from the session
    return redirect(url_for("login"))

@app.route('/dashboard/milk_collection', methods=["GET", "POST"])
@login_required
def milk_collection():
    cursor = None
    email = session.get('user_id')  # Initialize email from the session
    if request.method == "POST":
        # Collect data from the form
        farmer_id = request.form['farmer_id']
        snf = request.form['snf']
        fat = request.form['fat']
        milk = request.form['milk']
        animal_type = request.form['animal_type']
        collection_time_of_day = request.form['collection_time_of_day']

        try:
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the script
            RATES_CSV_PATH = os.path.join(BASE_DIR, "rates.csv")  # Construct a relative path
            dataframe = pd.read_csv(RATES_CSV_PATH)
            column_name = str(snf)  # Assuming snf corresponds to the column name in the CSV
            fat_value = float(fat)
            milk_type = animal_type.upper()

            def get_value(dataframe, column_name, fat_value, milk_type):
                # Ensure column_name exists in the dataframe
                if column_name not in dataframe.columns:
                    return f"Column '{column_name}' does not exist in the data."

                # Filter by TYPE and FAT
                filtered_data = dataframe[(dataframe['TYPE'] == milk_type) & (dataframe['FAT'] == fat_value)]

                if filtered_data.empty:
                    return f"No data found for TYPE='{milk_type}' and FAT={fat_value}."

                # Return the value from the specified column
                return filtered_data[column_name].values[0]

            # Retrieve rate
            rate = get_value(dataframe, column_name, fat_value, milk_type)
            if isinstance(rate, str):  # Check for error message
                flash(rate, "danger")
                return render_template("milk-collection.html")

            total_rate = float(milk) * float(rate)

            # Insert data into the database
            cursor = mysql.connection.cursor()
            que = """
                SELECT 1 FROM farmer_details 
                WHERE farmer_id = %s AND email = %s
            """
            cursor.execute(que, (farmer_id, email))
            check = cursor.fetchone()

            if check:
                query = """
                    INSERT INTO milk_collection (farmer_id, snf, fat, milk, animal_type, total_rate, collection_time_of_day, rate, email)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (farmer_id, snf, fat, milk, animal_type, total_rate, collection_time_of_day, rate, email))
                mysql.connection.commit()
                flash("Milk collection data added successfully!", "success")
            else:
                flash("Invalid farmer ID or email!", "danger")

        except Exception as e:
            flash(f"Error: {e}", "danger")
        finally:
            if cursor:  # Only close cursor if it's been initialized
                cursor.close()

    # Fetch the last 10 rows from the database
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT id,farmer_id, animal_type, snf, fat, milk, total_rate, collection_time,
                   CASE WHEN collection_time_of_day = 1 THEN 'Day' ELSE 'Night' END AS collection_time_of_day
            FROM milk_collection
            WHERE email = %s
            ORDER BY collection_time DESC
            LIMIT 10
        """, (email,))
        last_entries = cursor.fetchall()
    except Exception as e:
        flash(f"Error fetching data: {e}", "danger")
        last_entries = []
    finally:
        if cursor:
            cursor.close()

    # Render the template with fetched data
    return render_template("milk-collection.html", last_entries=last_entries)



from flask import Flask, request, redirect, render_template, flash, session
from flask_mysqldb import MySQL
import MySQLdb

@app.route('/add_farmer', methods=['GET', 'POST'])
@login_required
def add_farmer():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        account_no = request.form['account_no']
        ifsc_code = request.form['ifsc_code']
        bank_name = request.form['bank_name']
        aadhar_no = request.form['aadhar_no']
        ufarmid = request.form['ufarmid']
        mobile = request.form['mobile']
        village = request.form['village']
        email = session.get('user_id')

        if not email:
            flash("User session expired. Please log in again.", "warning")
            return redirect('/login')

        try:
            cursor = mysql.connection.cursor()
            query = """
                INSERT INTO farmer_details 
                (name, account_no, ifsc_code, bank_name, aadhar_no, ufarmid, mobile, village, email)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (name, account_no, ifsc_code, bank_name, aadhar_no, ufarmid, mobile, village, email))
            mysql.connection.commit()
            flash("Farmer added successfully!", "success")
        except MySQLdb.Error as err:
            flash(f"Database error: {err}", "danger")
        finally:
            cursor.close()  # No need to close mysql.connection

        return redirect('/dashboard')
    
    return render_template('add_farmer.html')



@app.route('/add_animal', methods=['GET', 'POST'])
@login_required
def add_animal():
    if request.method == 'POST':
        # Get form data
        name = request.form['farmer_id']
        account_no = request.form['animal_type']
        ifsc_code = request.form['cow_type']
        bank_name = request.form['tag_no']
        aadhar_no = request.form['uanimalid']

        # Insert data into the database
        try:
            cursor = mysql.connection.cursor()
            query = """
                INSERT INTO animal_details (farmer_id, animal_type, cow_type, tag_no, uanimalid)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (name, account_no, ifsc_code, bank_name, aadhar_no))
            mysql.connection.commit()
            flash("Animal added successfully!", "success")
        except mysql.connector.Error as err:
            flash(f"Error: {err}", "danger")
        finally:
            cursor.close()
            mysql.connection.close()

        return redirect('/dashboard')
    
    # Render the form
    return render_template('add_animal.html')



@app.route('/dashboard/billing', methods=['GET', 'POST'])
@login_required
def bill_page():
    results = None
    total = 0
    if request.method == 'POST':
        try:
            # Get form data
            farmer_id = int(request.form['farmer_id'])
            email = session.get('user_id')
            start_date = str(request.form['start_date'])
            end_date = str(request.form['end_date'])

            # SQL Queries
            query = """
            SELECT 
                farmer_id,
                animal_type,
                DATE(collection_time) AS collection_date,
                COALESCE(MAX(CASE WHEN collection_time_of_day = 1 THEN snf ELSE NULL END), 0) AS day_snf,
                COALESCE(MAX(CASE WHEN collection_time_of_day = 1 THEN fat ELSE NULL END), 0) AS day_fat,
                COALESCE(MAX(CASE WHEN collection_time_of_day = 1 THEN milk ELSE NULL END), 0) AS day_milk,
                COALESCE(MAX(CASE WHEN collection_time_of_day = 1 THEN rate ELSE NULL END), 0) AS day_rate,
                COALESCE(MAX(CASE WHEN collection_time_of_day = 1 THEN total_rate ELSE NULL END), 0) AS day_total_rate,
                COALESCE(MAX(CASE WHEN collection_time_of_day = 0 THEN snf ELSE NULL END), 0) AS night_snf,
                COALESCE(MAX(CASE WHEN collection_time_of_day = 0 THEN fat ELSE NULL END), 0) AS night_fat,
                COALESCE(MAX(CASE WHEN collection_time_of_day = 0 THEN milk ELSE NULL END), 0) AS night_milk,
                COALESCE(MAX(CASE WHEN collection_time_of_day = 0 THEN rate ELSE NULL END), 0) AS night_rate,
                COALESCE(MAX(CASE WHEN collection_time_of_day = 0 THEN total_rate ELSE NULL END), 0) AS night_total_rate,
                COALESCE(SUM(total_rate), 0) AS total
            FROM 
                milk_collection
            WHERE 
                farmer_id = %s AND email = %s 
                AND DATE(collection_time) BETWEEN %s AND %s
            GROUP BY 
                farmer_id, animal_type, DATE(collection_time)
            ORDER BY 
                collection_date;
            """
            query2 = """
            select sum(total_rate) as total
            FROM 
                milk_collection
            WHERE 
                farmer_id = %s AND email = %s 
                AND DATE(collection_time) BETWEEN %s AND %s
            """
            cur = mysql.connection.cursor()
            cur.execute(query, (farmer_id, email, start_date, end_date))
            results = cur.fetchall()
            cur.execute(query2, (farmer_id, email, start_date, end_date))
            tres = cur.fetchone()
            if tres==None:
                total = 0
            else: 
                total = round(tres[0],2)
            cur.close()

        except Exception as e:
            flash(f"Error: {e}", "danger")
    return render_template('billing.html', results=results, total=total)




@app.route('/transaction')
@login_required
def Transaction():
    return render_template("transaction.html")


@app.route('/dashboard/Banking', methods=['GET', 'POST'])
@login_required
def Add_transaction():
    if request.method == 'POST':
        # Get form data
        farmer_id = request.form['farmer_id']
        amount = request.form['Amount']
        notes = request.form['Reason']
        transaction_type = request.form['transaction_type']
        email = session.get('user_id')  # Logged-in user's email

        try:
            cursor = mysql.connection.cursor()

            query = """
                SELECT 1 FROM farmer_details 
                WHERE farmer_id = %s AND email = %s
            """
            cursor.execute(query, (farmer_id, email))
            result = cursor.fetchone()

            if result: 
                insert_query = """
                    INSERT INTO Transactions (farmer_id, transaction_type, amount, notes, email)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (farmer_id, transaction_type, amount, notes, email))
                mysql.connection.commit()
                flash("Transaction Complete!", "success")
            else:
                flash("Invalid farmer ID or email!", "danger")

        except mysql.connector.Error as err:
            flash(f"Database Error: {err}", "danger")
        finally:
            cursor.close()

        return render_template('banking.html')

    return render_template('banking.html')


@app.route('/dashboard/Banking/transaction', methods=['GET', 'POST'])
@login_required
def Trans_hist():
    total = 0
    email = session.get("user_id")
    results = []
    farmer_id = None

    if request.method == 'POST':
        farmer_id = request.form.get('farmer_id')
    elif request.method == 'GET':
        farmer_id = request.args.get('farmer_id')

    if farmer_id:
        try:
            cursor = mysql.connection.cursor()

            # Fetch transaction history
            query = """SELECT transaction_id, transaction_type, amount, notes, transaction_date  
                       FROM transactions WHERE farmer_id = %s AND email = %s"""
            cursor.execute(query, (farmer_id, email))
            results = cursor.fetchall()

            # Fetch total deposit and withdrawal
            query1 = """SELECT 
                            COALESCE(SUM(CASE WHEN transaction_type = 'Deposit' THEN amount ELSE 0 END), 0) AS deposit_amount,
                            COALESCE(SUM(CASE WHEN transaction_type = 'Withdraw' THEN amount ELSE 0 END), 0) AS withdrawal_amount
                        FROM transactions 
                        WHERE farmer_id = %s AND email = %s"""
            cursor.execute(query1, (farmer_id, email))
            amt = cursor.fetchone() or (0, 0)  # Ensuring None is replaced with (0,0)

            # Calculate total balance
            total = amt[0] - amt[1]

        except Exception as e:
            flash(f"Database Error: {e}", "danger")
        finally:
            cursor.close()

    return render_template("transaction.html", results=results, total=total)

@app.route('/dashboard/milk_collection/wrong_entry', methods=['GET', 'POST'])
@login_required
def del_entry():
    email = session.get("user_id")
    id = None
    farmer_id = None

    if request.method == 'POST':
        farmer_id = request.form.get('farmer_id')
        id = request.form.get('id')
    elif request.method == 'GET':
        farmer_id = request.args.get('farmer_id')
        id = request.args.get('id')

    if farmer_id and id:
        try:
            cursor = mysql.connection.cursor()
            query = """SELECT 1 FROM milk_collection WHERE farmer_id = %s AND email = %s"""
            cursor.execute(query, (farmer_id, email))
            check = cursor.fetchone()

            if check:
                query1 = """DELETE FROM milk_collection WHERE farmer_id = %s AND id = %s AND email = %s"""
                cursor.execute(query1, (farmer_id, id, email))
                mysql.connection.commit() 
                flash("Record successfully deleted", "success")
                return redirect(url_for("milk_collection")) 
            else:
                flash("Record not found, or check the entered ID", "warning")
        
        except Exception as e:
            mysql.connection.rollback()  
            app.logger.error(f"Database Error: {e}")
            flash("An error occurred while deleting the record", "danger")

        finally:
            cursor.close() 

    return render_template("wrong.html")

@app.route('/remove', methods=['GET', 'POST'])
@login_required
def remove_farmer():
    email = session.get("user_id")
    farmer_id = None

    if request.method == 'POST':
        farmer_id = request.form.get('farmer_id')

    if farmer_id:
        try:
            cursor = mysql.connection.cursor()

            # Check if farmer exists
            cursor.execute("SELECT COUNT(*) FROM farmer_details WHERE farmer_id = %s AND email = %s", (farmer_id, email))
            farmer_exists = cursor.fetchone()[0]

            if farmer_exists:
                # Check if farmer has associated records in milk_collection
                cursor.execute("SELECT COUNT(*) FROM milk_collection WHERE farmer_id = %s", (farmer_id,))
                milk_records = cursor.fetchone()[0]

                if milk_records:
                    flash("This farmer has linked records. If you continue, data will be deleted.", "warning")

                # Proceed with deletion
                cursor.execute("DELETE FROM farmer_details WHERE farmer_id = %s AND email = %s", (farmer_id, email))
                mysql.connection.commit()
                flash("Farmer record successfully deleted", "success")
                return redirect(url_for("dashboard"))

            else:
                flash("Farmer not found, please check the entered ID.", "warning")

        except Exception as e:
            mysql.connection.rollback()
            app.logger.error(f"Database Error: {e}", exc_info=True)
            flash("An error occurred while deleting the farmer record.", "danger")

        finally:
            cursor.close()

    return render_template("remove_farmer.html")

@app.route('/view')
@login_required
def view_farmers():
    email = session.get("user_id")
    try:
        cursor = mysql.connection.cursor()
        query = "SELECT farmer_id, name, account_no, ifsc_code, bank_name, aadhar_no, mobile, village FROM farmer_details WHERE email = %s"
        cursor.execute(query, (email,))  # Ensure the email is passed as a tuple
        farmers = cursor.fetchall()
        cursor.close()
    except Exception as e:
        flash(f"Database Error: {e}", "danger")
        farmers = []

    return render_template("view_farmer.html", farmers=farmers)



if __name__ == "__main__":
    app.run(debug=True)
 
