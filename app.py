from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import config
import os

app = Flask(__name__)

# ================= SECRET KEY =================

app.secret_key = "musicbandsecretkey"

# ================= UPLOAD FOLDER =================

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ================= MYSQL CONFIG =================

app.config['MYSQL_HOST'] = config.MYSQL_HOST
app.config['MYSQL_USER'] = config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = config.MYSQL_DB

mysql = MySQL(app)


# ================= HOME PAGE =================

@app.route('/')
def home():

    search = request.args.get('search')
    category = request.args.get('category')

    cur = mysql.connection.cursor()

    query = "SELECT * FROM bands WHERE 1=1"
    values = []

    # Search
    if search:
        query += " AND band_name LIKE %s"
        values.append('%' + search + '%')

    # Filter
    if category and category != "All":
        query += " AND category=%s"
        values.append(category)

    cur.execute(query, tuple(values))

    bands = cur.fetchall()

    # Categories
    cur.execute("SELECT DISTINCT category FROM bands")

    categories = cur.fetchall()

    # Reviews
    cur.execute(
        """
        SELECT
        users.fullname,
        reviews.rating,
        reviews.review

        FROM reviews

        JOIN users
        ON reviews.user_id = users.id

        ORDER BY reviews.id DESC
        """
    )

    reviews = cur.fetchall()

    cur.close()

    return render_template(
        'index.html',
        bands=bands,
        categories=categories,
        reviews=reviews
    )
# ================= USER REGISTER =================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        fullname = request.form['fullname']
        email = request.form['email']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO users(fullname, email, password)
            VALUES(%s, %s, %s)
            """,
            (fullname, email, hashed_password)
        )

        mysql.connection.commit()

        cur.close()

        return redirect('/login')

    return render_template('register.html')

# ================= USER LOGIN =================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cur.fetchone()

        cur.close()

        if user:

            stored_password = user[3]

            if check_password_hash(stored_password, password):

                session['user_id'] = user[0]
                session['user_name'] = user[1]

                return redirect('/dashboard')

        return "Invalid Email or Password"

    return render_template('login.html')

# ================= USER DASHBOARD =================

@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    return render_template('dashboard.html')

# ================= USER LOGOUT =================

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')

# ================= ADMIN LOGIN =================

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()

        cur.execute(
            """
            SELECT * FROM admins
            WHERE email=%s AND password=%s
            """,
            (email, password)
        )

        admin = cur.fetchone()

        cur.close()

        if admin:

            session['admin'] = admin[1]

            return redirect('/admin-dashboard')

        return "Invalid Email or Password"

    return render_template('admin_login.html')

# ================= ADMIN DASHBOARD =================

@app.route('/admin-dashboard')
def admin_dashboard():

    if 'admin' not in session:
        return redirect('/admin-login')

    cur = mysql.connection.cursor()

    # Total Users
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    # Total Bands
    cur.execute("SELECT COUNT(*) FROM bands")
    total_bands = cur.fetchone()[0]

    # Total Bookings
    cur.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = cur.fetchone()[0]

    cur.close()

    return render_template(
        'admin_dashboard.html',
        total_users=total_users,
        total_bands=total_bands,
        total_bookings=total_bookings
    )

# ================= ADMIN LOGOUT =================

@app.route('/admin-logout')
def admin_logout():

    session.pop('admin', None)

    return redirect('/admin-login')

# ================= ADD BAND =================

@app.route('/add-band', methods=['GET', 'POST'])
def add_band():

    if 'admin' not in session:
        return redirect('/admin-login')

    if request.method == 'POST':

        band_name = request.form['band_name']
        category = request.form['category']
        description = request.form['description']
        price = request.form['price']

        image = request.files['image']

        filename = secure_filename(image.filename)

        image.save(
            os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )
        )

        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO bands
            (band_name, category, description, image, price)
            VALUES(%s, %s, %s, %s, %s)
            """,
            (
                band_name,
                category,
                description,
                filename,
                price
            )
        )

        mysql.connection.commit()

        cur.close()

        return "Band Added Successfully"

    return render_template('add_band.html')

# ================= MANAGE BANDS =================

@app.route('/manage-bands')
def manage_bands():

    if 'admin' not in session:
        return redirect('/admin-login')

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM bands")

    bands = cur.fetchall()

    cur.close()

    return render_template(
        'manage_bands.html',
        bands=bands
    )

# ================= DELETE BAND =================

@app.route('/delete-band/<int:id>')
def delete_band(id):

    if 'admin' not in session:
        return redirect('/admin-login')

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM bands WHERE id=%s",
        (id,)
    )

    mysql.connection.commit()

    cur.close()

    return redirect('/manage-bands')

# ================= EDIT BAND =================

@app.route('/edit-band/<int:id>', methods=['GET', 'POST'])
def edit_band(id):

    if 'admin' not in session:
        return redirect('/admin-login')

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT * FROM bands WHERE id=%s",
        (id,)
    )

    band = cur.fetchone()

    if request.method == 'POST':

        band_name = request.form['band_name']
        category = request.form['category']
        description = request.form['description']
        price = request.form['price']

        cur.execute(
            """
            UPDATE bands
            SET band_name=%s,
                category=%s,
                description=%s,
                price=%s
            WHERE id=%s
            """,
            (
                band_name,
                category,
                description,
                price,
                id
            )
        )

        mysql.connection.commit()

        cur.close()

        return redirect('/manage-bands')

    return render_template(
        'edit_band.html',
        band=band
    )

# ================= BOOK BAND =================

@app.route('/book-band/<int:band_id>', methods=['GET', 'POST'])
def book_band(band_id):

    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    # Get Band
    cur.execute(
        "SELECT * FROM bands WHERE id=%s",
        (band_id,)
    )

    band = cur.fetchone()

    # Get unavailable dates
    cur.execute(
        """
        SELECT event_date
        FROM bookings
        WHERE band_id=%s
        AND status != 'Rejected'
        """,
        (band_id,)
    )

    unavailable_dates = cur.fetchall()

    if request.method == 'POST':

        event_date = request.form['event_date']
        event_location = request.form['event_location']
        message = request.form['message']

        # Check existing booking
        cur.execute(
            """
            SELECT * FROM bookings
            WHERE band_id=%s
            AND event_date=%s
            AND status != 'Rejected'
            """,
            (band_id, event_date)
        )

        existing_booking = cur.fetchone()

        # Already booked
        if existing_booking:

            return "This band is already booked on this date."

        # Save booking
        cur.execute(
            """
            INSERT INTO bookings
            (user_id, band_id, event_date, event_location, message)
            VALUES(%s, %s, %s, %s, %s)
            """,
            (
                session['user_id'],
                band_id,
                event_date,
                event_location,
                message
            )
        )

        mysql.connection.commit()

        cur.close()

        return "Booking Submitted Successfully"

    return render_template(
        'book_band.html',
        band=band,
        unavailable_dates=unavailable_dates
    )
# ================= MY BOOKINGS =================

@app.route('/my-bookings')
def my_bookings():

    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        """
        SELECT
        bands.band_name,
        bookings.event_date,
        bookings.event_location,
        bookings.status

        FROM bookings

        JOIN bands
        ON bookings.band_id = bands.id

        WHERE bookings.user_id=%s
        """,
        (session['user_id'],)
    )

    bookings = cur.fetchall()

    cur.close()

    return render_template(
        'my_bookings.html',
        bookings=bookings
    )

# ================= ADMIN BOOKINGS =================

@app.route('/admin-bookings')
def admin_bookings():

    if 'admin' not in session:
        return redirect('/admin-login')

    cur = mysql.connection.cursor()

    cur.execute(
        """
        SELECT bookings.*, bands.band_name

        FROM bookings

        JOIN bands
        ON bookings.band_id = bands.id
        """
    )

    bookings = cur.fetchall()

    cur.close()

    return render_template(
        'admin_bookings.html',
        bookings=bookings
    )

# ================= UPDATE BOOKING STATUS =================

@app.route('/update-booking/<int:id>/<status>')
def update_booking(id, status):

    if 'admin' not in session:
        return redirect('/admin-login')

    cur = mysql.connection.cursor()

    cur.execute(
        """
        UPDATE bookings
        SET status=%s
        WHERE id=%s
        """,
        (status, id)
    )

    mysql.connection.commit()

    cur.close()

    return redirect('/admin-bookings')

# ================= PAYMENT =================

@app.route('/payment/<int:band_id>')
def payment(band_id):

    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT * FROM bands WHERE id=%s",
        (band_id,)
    )

    band = cur.fetchone()

    cur.close()

    amount = int(band[5]) * 100

    return render_template(
        'payment.html',
        key=config.RAZORPAY_KEY_ID,
        amount=amount
    )

# ================= PAYMENT SUCCESS =================

@app.route('/payment-success')
def payment_success():

    return "Payment Successful & Booking Confirmed"

# ================= CONTACT PAGE =================

@app.route('/contact', methods=['GET', 'POST'])
def contact():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']

        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO contact_messages
            (name, email, subject, message)
            VALUES(%s, %s, %s, %s)
            """,
            (name, email, subject, message)
        )

        mysql.connection.commit()

        cur.close()

        return "Message Sent Successfully"

    return render_template('contact.html')

# ================= ADMIN MESSAGES =================

@app.route('/admin-messages')
def admin_messages():

    if 'admin' not in session:
        return redirect('/admin-login')

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM contact_messages")

    messages = cur.fetchall()

    cur.close()

    return render_template(
        'admin_messages.html',
        messages=messages
    )
    
    # ================= ADD REVIEW =================

@app.route('/add-review/<int:band_id>', methods=['GET', 'POST'])
def add_review(band_id):

    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    # Get Band
    cur.execute(
        "SELECT * FROM bands WHERE id=%s",
        (band_id,)
    )

    band = cur.fetchone()

    if request.method == 'POST':

        rating = request.form['rating']
        review = request.form['review']

        cur.execute(
            """
            INSERT INTO reviews
            (user_id, band_id, rating, review)
            VALUES(%s, %s, %s, %s)
            """,
            (
                session['user_id'],
                band_id,
                rating,
                review
            )
        )

        mysql.connection.commit()

        cur.close()

        return "Review Added Successfully"

    return render_template(
        'add_review.html',
        band=band
    )
    
    # ================= USER PROFILE =================

@app.route('/profile', methods=['GET', 'POST'])
def profile():

    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    # Get User
    cur.execute(
        "SELECT * FROM users WHERE id=%s",
        (session['user_id'],)
    )

    user = cur.fetchone()

    # Update Profile
    if request.method == 'POST':

        fullname = request.form['fullname']
        email = request.form['email']
        password = request.form['password']

        # If password entered
        if password:

            hashed_password = generate_password_hash(password)

            cur.execute(
                """
                UPDATE users
                SET fullname=%s,
                    email=%s,
                    password=%s
                WHERE id=%s
                """,
                (
                    fullname,
                    email,
                    hashed_password,
                    session['user_id']
                )
            )

        else:

            cur.execute(
                """
                UPDATE users
                SET fullname=%s,
                    email=%s
                WHERE id=%s
                """,
                (
                    fullname,
                    email,
                    session['user_id']
                )
            )

        mysql.connection.commit()

        # Update session name
        session['user_name'] = fullname

        cur.close()

        return redirect('/dashboard')

    return render_template(
        'profile.html',
        user=user
    )

# ================= SETTINGS PAGE =================

@app.route('/settings')
def settings():

    if 'user_id' not in session:
        return redirect('/login')

    return render_template('settings.html')

# ================= DELETE BOOKINGS =================

@app.route('/delete-bookings')
def delete_bookings():

    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM bookings WHERE user_id=%s",
        (session['user_id'],)
    )

    mysql.connection.commit()

    cur.close()

    return "Booking History Deleted Successfully"

# ================= DELETE ACCOUNT =================

@app.route('/delete-account')
def delete_account():

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    cur = mysql.connection.cursor()

    # Delete bookings
    cur.execute(
        "DELETE FROM bookings WHERE user_id=%s",
        (user_id,)
    )

    # Delete reviews
    cur.execute(
        "DELETE FROM reviews WHERE user_id=%s",
        (user_id,)
    )

    # Delete user
    cur.execute(
        "DELETE FROM users WHERE id=%s",
        (user_id,)
    )

    mysql.connection.commit()

    cur.close()

    # Logout user
    session.clear()

    return redirect('/')

# ================= MANAGE USERS =================

@app.route('/manage-users')
def manage_users():

    if 'admin' not in session:
        return redirect('/admin-login')

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM users")

    users = cur.fetchall()

    cur.close()

    return render_template(
        'manage_users.html',
        users=users
    )
    
    # ================= DELETE USER =================

@app.route('/delete-user/<int:id>')
def delete_user(id):

    if 'admin' not in session:
        return redirect('/admin-login')

    cur = mysql.connection.cursor()

    # Delete bookings
    cur.execute(
        "DELETE FROM bookings WHERE user_id=%s",
        (id,)
    )

    # Delete reviews
    cur.execute(
        "DELETE FROM reviews WHERE user_id=%s",
        (id,)
    )

    # Delete user
    cur.execute(
        "DELETE FROM users WHERE id=%s",
        (id,)
    )

    mysql.connection.commit()

    cur.close()

    return redirect('/manage-users')

# ================= RUN APP =================

if __name__ == '__main__':
    app.run(debug=True)