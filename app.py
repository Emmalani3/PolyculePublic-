import os
import io

import base64
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify, send_file
from flask_session import Session
from PIL import Image
import sqlite3
from typing import List, Dict
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from helpers import apology, login_required, get_profile_lists, allowed_file, search_users

# Configure application
app = Flask(__name__)



# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///polycule.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show user profile"""
    #display table with users stocks, number of shares, current price of each stock, total value of stock shares X price,
    #display client current cash balance
    lists = get_profile_lists()
    user_clid = session["user_CLID"]
    rows = db.execute("SELECT * FROM profile WHERE users_CLID = ?", user_clid)
    contact_rows = db.execute("SELECT * FROM contact Where users_CLID = ?", user_clid)
    age = db.execute("SELECT strftime('%Y', 'now') - strftime('%Y', dateOfBirth) AS age FROM profile WHERE users_CLID = ?", user_clid)
    if rows:
        profile_data = rows[0]
        #print(profile_data)
    else:
        profile_data = {}

    if contact_rows:
        contact_data = contact_rows[0]
        #print(contact_data)
    else:
        contact_data = {}
    return render_template("index.html", profile=profile_data, contact=contact_data, age=age, **lists)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
#NOT WORKING thinks its supposed to be a list not a dict?

    #For each row, make clear whether a stock was bought or sold and include the stock’s symbol,
    # the (purchase or sale) price, the number of shares bought or sold, and the date and time at which the transaction occurred.
    #You might need to alter the table you created for buy or supplement it with an additional table. Try to minimize redundancies.
    stock_data = get_portfolio_history(session["user_id"])
    return render_template("history.html", stocks=stock_data, usd=usd)
    #return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )


        # Ensure username exists and password is correct
        #print("Stored hash:", rows[0]["passwordHash"])
        #print("Entered password:", request.form.get("password"))
        if len(rows) != 1 or not check_password_hash(
            rows[0]["passwordHash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_CLID"] = rows[0]["CLID"]
        #print("Session user_CLID set to:", session["user_CLID"])
        if len(rows) == 0:
            print("No user found with the provided credentials.")
        else:
            #print("Stored hash:", rows[0]["passwordHash"])
        # Redirect user to home page
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    error_message = None

    if request.method == 'GET':
        return render_template('register.html', error_message=error_message)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        confirmation = request.form.get('confirmation')
        policy = request.form.get('policy')
        tos = request.form.get('tos')

        if not username or not password or not confirmation or not email or not policy or not tos:
            error_message = "All fields are required."
            return redirect(url_for('register', error_message=error_message))

        if password != confirmation:
            error_message = "Password and Confirmation must match."
            return redirect(url_for('register', error_message=error_message))

        hashed_password = generate_password_hash(password)
        # Check that username is unique using try and except
        try:
            user = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
            if user:
                error_message = "Username is already taken. Please choose another"
                return redirect(url_for('register', error_message=error_message))


            hashed_password = generate_password_hash(request.form.get("password"))
            try:
                # Add username and password to users
                db.execute("INSERT INTO users (username, passwordHash) VALUES(?, ?)", request.form.get("username"), hashed_password)
                print("User registration successfully")
                return render_template("login.html")
            except Exception as e:
                error_message ="Error inserting user:"
                return render_template("register.html", error_message=error_message)

        except Exception as e:
            error_message = "Error checking username"
            return render_template("register.html", error_message=error_message)


@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    """Update Password for user"""
    if request.method == "POST":

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide password", 403)

        # Check that the password and confirmation match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Password and Confirmation must match.", 403)

        # Add username and password to users
        hashed_password = generate_password_hash(request.form.get("password"))
        db.execute("UPDATE users SET passwordHash = ? WHERE CLID = ?", hashed_password, session["user_CLID"])
        return redirect("/")
    else:
        return render_template("password.html")


@app.route("/profile", methods=["GET", "POST"])
@login_required
def your_route():
    lists = get_profile_lists()
    user_clid = session["user_CLID"]

    rows = db.execute("SELECT * FROM profile WHERE users_CLID = ?", user_clid)
    contact_rows = db.execute("SELECT * FROM contact WHERE users_CLID = ?", user_clid)
    age = db.execute("SELECT strftime('%Y', 'now') - strftime('%Y', dateOfBirth) AS age FROM profile WHERE users_CLID = ?", user_clid)

    if rows:
        profile_data = rows[0]
        #print(profile_data)
    else:
        profile_data = {}

    if contact_rows:
        contact_data = contact_rows[0]
        #print(contact_data)
    else:
        contact_data = {}

    # Prepare photo for display
    if profile_data and profile_data.get('photo'):
        profile_data['photo'] = f"data:image/jpeg;base64,{base64.b64encode(profile_data['photo']).decode('utf-8')}"

    return render_template("profile.html", profile=profile_data, contact=contact_data, age=age, **lists)


@app.route("/updateprofile", methods=["GET", "POST"])
@login_required
def updateprofile():
    """Update Password for user"""
    lists = get_profile_lists()
    user_clid = session["user_CLID"]

    if request.method == "POST":
        # auto fill data from saved
        visibility = request.form.get("visibility")
        visibility_on_search = 1 if visibility == 'Yes' else 0

        feet = request.form.get("feet")
        inches = request.form.get("inches")

        if feet and inches:
            feet = int(feet)
            inches = int(inches)
            total_inches = (feet * 12) + inches
        else:
            total_inches = None

        form_data = {key: request.form.get(key) or None for key in request.form}
        values = [form_data.get(key) for key in ["biography", "dateOfBirth", "displayName", "feet", "inches", "drinking", "drugs", "education", "ethnicity", "gender", "hasKids", "languages", "location", "marijuana", "occupation", "pets", "polyPreference", "pronouns", "religion" "sexualOrientation", "smoking", "vaping", "wantsKids", "currentlyPartnered", "numCurrentPartners", "maxPartners"]]

        rows = db.execute("SELECT * FROM profile WHERE users_CLID = ?", user_clid)
        contact_rows = db.execute("SELECT * FROM contact WHERE users_CLID = ?", user_clid)
        if rows:
            profile_data = rows[0]
            if profile_data.get('languages'):
                profile_data['languages'] = profile_data['languages'].split(',')
            else:
                profile_data['languages'] = []

            if profile_data.get('pets'):
                profile_data['pets'] = profile_data['pets'].split(',')
            else:
                profile_data['pets'] = []
        else:
            profile_data = {}

        if contact_rows:
            contact_data = contact_rows[0]
            #print(contact_data)
        else:
            contact_data = {}

        # Prepare photo for display
        if profile_data and profile_data.get('photo'):
            profile_data['photo'] = f"data:image/jpeg;base64,{base64.b64encode(profile_data['photo']).decode('utf-8')}"
        # create or update existing line
        db.execute("""
            INSERT INTO profile (users_CLID, visibility_on_search, displayName, gender, height, biography,
            location, ethnicity, pronouns, sexualOrientation, polyPreference, smoking, vaping, marijuana,
            drugs, drinking, hasKids, wantsKids, religion, pets, languages, education, dateOfBirth,
            occupation, currentlyPartnered, numCurrentPartners, maxPartners)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(users_CLID) DO UPDATE SET
            visibility_on_search = excluded.visibility_on_search,
            displayName = excluded.displayName,
            gender = excluded.gender,
            height = excluded.height,
            biography = excluded.biography,
            location = excluded.location,
            ethnicity = excluded.ethnicity,
            pronouns = excluded.pronouns,
            sexualOrientation = excluded.sexualOrientation,
            polyPreference = excluded.polyPreference,
            smoking = excluded.smoking,
            vaping = excluded.vaping,
            marijuana = excluded.marijuana,
            drugs = excluded.drugs,
            drinking = excluded.drinking,
            hasKids = excluded.hasKids,
            wantsKids = excluded.wantsKids,
            religion = excluded.religion,
            pets = excluded.pets,
            languages = excluded.languages,
            education = excluded.education,
            dateOfBirth = excluded.dateOfBirth,
            occupation = excluded.occupation,
            currentlyPartnered = excluded.currentlyPartnered,
            numCurrentPartners = excluded.numCurrentPartners,
            maxPartners = excluded.maxPartners
        """, user_clid, visibility_on_search, request.form.get("displayName"), request.form.get("gender"),
        total_inches, request.form.get("biography"), request.form.get("location"), request.form.get("ethnicity"),
        request.form.get("pronouns"), request.form.get("sexualOrientation"), request.form.get("polyPreference"),
        request.form.get("smoking"), request.form.get("vaping"), request.form.get("marijuana"),
        request.form.get("drugs"), request.form.get("drinking"), request.form.get("hasKids"),
        request.form.get("wantsKids"), request.form.get("religion"), request.form.get("pets"),
        request.form.get("languages"), request.form.get("education"), request.form.get("dateOfBirth"),
        request.form.get("occupation"), request.form.get("currentlyPartnered"), request.form.get("numCurrentPartners"),
        request.form.get("maxPartners"))
        #db.execute("""
         #   INSERT INTO contact (users_CLID, nameFirst, nameLast, Email, phoneNumber)
          #  VALUES (?, ?, ?, ?, ?)
           # ON CONFLICT(users_CLID) DO UPDATE SET
            #nameFirst = excluded.nameFirst,
            #nameLast = excluded.nameLast,
            #Email = excluded.Email,
            #phoneNumber = excluded.phoneNumber
      #  """, user_clid, request.form.get("nameFirst"), request.form.get("nameLast"), request.form.get("Email"), request.form.get("phoneNumber"))

        return render_template("updateprofile.html", profile=profile_data, contact=contact_data, **lists)
    else:
        rows = db.execute("SELECT * FROM profile WHERE users_CLID = ?", user_clid)
        contact_rows = db.execute("SELECT * FROM contact Where users_CLID = ?", user_clid)
        if rows:
            profile_data = rows[0]
            #print(profile_data)
        else:
            profile_data = {}

        if contact_rows:
            contact_data = contact_rows[0]
            #print(contact_data)
        else:
            contact_data = {}
        #coppied from above Prepare photo for display
        if profile_data and profile_data.get('photo'):
            profile_data['photo'] = f"data:image/jpeg;base64,{base64.b64encode(profile_data['photo']).decode('utf-8')}"

        return render_template("updateprofile.html", profile=profile_data, contact=contact_data, **lists)


@app.template_filter('b64encode')
def b64encode(data):
    """Encode binary data to base64 for rendering in templates."""
    return base64.b64encode(data).decode('utf-8')


@app.route("/uploadphoto", methods=["GET", "POST"])
@login_required
def uploadphoto():
    """Upload photo for user"""
    error_message = None

    lists = get_profile_lists()
    user_clid = session["user_CLID"]
    profile_data = {}
    app.config['UPLOAD_FOLDER'] = 'static/clientUploads'

    if request.method == "POST":
        if 'photo' not in request.files:
             error_message = "No file part?"
        file = request.files['photo']
        if file.filename == '':
             error_message = "Password and Confirmation must match."
        # Save the file or process it here
         # Save the image data directly to the database as binary
        if file and allowed_file(file.filename):
            with Image.open(file) as img:
                img = img.convert("RGB")  # Ensure consistency in color format

                # Calculate the aspect ratio of the image
                original_width, original_height = img.size
                aspect_ratio = original_width / original_height

                target_width, target_height = 300, 300
                target_aspect_ratio = target_width / target_height

                # Resize while preserving aspect ratio
                if aspect_ratio > target_aspect_ratio:
                    # Wider than target: Resize by height and crop width
                    new_height = target_height
                    new_width = int(target_height * aspect_ratio)
                else:
                    # Taller than target: Resize by width and crop height
                    new_width = target_width
                    new_height = int(target_width / aspect_ratio)

                img = img.resize((new_width, new_height), Image.LANCZOS)

                # Center-crop the resized image
                left = (new_width - target_width) / 2
                top = (new_height - target_height) / 2
                right = (new_width + target_width) / 2
                bottom = (new_height + target_height) / 2
                img = img.crop((left, top, right, bottom))

                # Save the processed image to an in-memory bytes buffer
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')  # Save as JPEG
                img_data = img_byte_arr.getvalue()  # Get binary data from the buffer

            # Save the binary image data to the database
            db.execute("""
                INSERT INTO profile (users_CLID, Photo)
                VALUES (?, ?)
                ON CONFLICT(users_CLID) DO UPDATE SET
                Photo = excluded.Photo
            """, user_clid, img_data)
        #coppied from above Prepare photo for display
        if profile_data and profile_data.get('photo'):
            profile_data['photo'] = f"data:image/jpeg;base64,{base64.b64encode(profile_data['photo']).decode('utf-8')}"

        return redirect(url_for('uploadphoto', error_message=error_message))

    # Retrieve profile data, including the image, from the database
    rows = db.execute("SELECT * FROM profile WHERE users_CLID = ?", user_clid)
    if rows:
        profile_data = rows[0]
    #coppied from above Prepare photo for display
    if profile_data and profile_data.get('photo'):
        profile_data['photo'] = f"data:image/jpeg;base64,{base64.b64encode(profile_data['photo']).decode('utf-8')}"

    return render_template("uploadphoto.html", profile=profile_data, **lists, error_message=error_message)

@app.route('/uploadpdf', methods=['GET', 'POST'])
def upload_pdf():
    """Uploat PDF"""
    lists = get_profile_lists()
    user_clid = session["user_CLID"]
    profile_data = {}
    app.config['UPLOAD_FOLDER'] = 'static/clientUploads'
    pdf_url = None

    error = None
    if 'pdf' not in request.files:
        error = "No pdf file"
    else:
        file = request.files['pdf']
        if file.filename == '':
            error = "No selected file"
        elif not file.filename.endswith('.pdf'):
            error = "Invalid file format. Only PDFs are allowed."
        else:
            # Save file locally for preview (optional step)
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])

            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)


            # Save the file to the database
        rows = db.execute("SELECT * FROM profile WHERE users_CLID = ?", user_clid)
        if rows:
            profile_data = rows[0]
            #print(profile_data)

        db.execute("""
            INSERT INTO profile (users_CLID, STD_STI_Tests)
            VALUES (?, ?)
            ON CONFLICT(users_CLID) DO UPDATE SET
            STD_STI_Tests = excluded.STD_STI_Tests
        """, user_clid, file_path)

        pdf_url = url_for('static', filename=f'uploadpdf/{file.filename}')

        return render_template('uploadpdf.html', error=error, profile=profile_data, **lists, pdf_url=pdf_url)

    return render_template('uploadpdf.html', error=error, profile=profile_data, **lists, pdf_url=pdf_url)

@app.route('/search', methods=['GET', 'POST'])
def search():
    lists = get_profile_lists()
    user_clid = session.get("user_CLID", None)  # Ensure session key exists
    profiles = []

    # Connect to the database
    conn = sqlite3.connect('polycule.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()


    if request.method == 'GET':
        try:
            # Collect form inputs
#            age_min = request.args.get('age_min', None)
 #           age_max = request.args.get('age_max', None)
  #          height_feet = request.args.get('heightFeet', None)
   #         height_inch = request.args.get('heightInch', None)
            education = request.args.getlist('education')
            ethnicity = request.args.getlist('ethnicity')
            location = request.args.getlist('location')
    #        religion = request.args.getlist('religion')
            hasKids = request.args.getlist('hasKids')
            wantsKids = request.args.getlist('wantsKids')
            pets = request.args.getlist('pets')
            languages = request.args.getlist('languages')
            gender = request.args.getlist('gender')
            sexualOrientation = request.args.getlist('sexualOrientation')
            polyPreference = request.args.getlist('polyPreference')
            marijuana = request.args.getlist('marijuana')
            smoking = request.args.getlist('smoking')
            drugs = request.args.getlist('drugs')
            drinking = request.args.getlist('drinking')
            vaping = request.args.getlist('vaping')

             # Build query
            query = "SELECT * FROM profile WHERE 1=1 AND visibility_on_search = 1"
            params = {}

            # Build query filters dynamically
#            if age_min and age_max:
 #               query +="""
  #                  AND CAST((strftime('%Y', 'now') - strftime('%Y', dateOfBirth)) -
   #                 (strftime('%m-%d', 'now') < strftime('%m-%d', dateOfBirth)) AS INTEGER)
    #                BETWEEN ? AND ?
     #           """
      #          params['age_min'] = age_min  # Minimum age
       #         params['age_max'] = age_max  # Maximum age

        #        if age_min is not None and age_max is not None:
                    # Ensure they are integers
         #           age_min = int(age_min)
          #          age_max = int(age_max)

            if drinking:
                query += " AND drinking IN ({})".format(','.join(['?'] * len(drinking)))
                params['drinking'] = drinking  # Add all selected drinking options
            else:
                # No drinking filter; select all drinking options by default (omit the clause)
                pass

            if drugs:
                query += " AND drugs IN ({})".format(','.join(['?'] * len(drugs)))
                params['drugs'] = drugs  # Add all selected drug options
            else:
                # No drugs filter; select all drug options by default (omit the clause)
                pass

            if education:
                query += " AND education IN ({})".format(','.join(['?'] * len(education)))
                params['education'] = education  # Add all selected education levels
            else:
                # No education filter; select all education levels by default (omit the clause)
                pass

            if ethnicity:
                query += " AND ethnicity IN ({})".format(','.join(['?'] * len(ethnicity)))
                params['ethnicity'] = ethnicity  # Add all selected ethnicities
            else:
                # No ethnicity filter; select all ethnicities by default (omit the clause)
                pass

            if gender:
                query += " AND gender IN ({})".format(','.join(['?'] * len(gender)))
                params['gender'] = gender  # Add all selected genders
            else:
                # No gender filter; select all genders by default (omit the clause)
                pass

            if hasKids:
                query += " AND has_kids IN ({})".format(','.join(['?'] * len(hasKids)))
                params['has_kids'] = hasKids  # Add all selected hasKids options
            else:
                # No hasKids filter; select all options by default (omit the clause)
                pass

  #          if height_feet or height_inch:
   #             min_height = int(height_feet or 0) * 12 + int(height_inch or 0)
    #            query += " AND height >= ?"
     #           params['height'] = min_height  # Minimum height in inches
      #      else:
       #         # No height filter; select all heights by default (omit the clause)
        #        pass

            if languages:
                query += " AND languages IN ({})".format(','.join(['?'] * len(languages)))
                params['languages'] = languages  # Add all selected languages
            else:
                # No languages filter; select all languages by default (omit the clause)
                pass

            if location:
                query += " AND location IN ({})".format(','.join(['?'] * len(location)))
                params['location'] = location  # Add all selected locations
            else:
                # No location filter; select all locations by default (omit the clause)
                pass

            if marijuana:
                query += " AND marijuana IN ({})".format(','.join(['?'] * len(marijuana)))
                params['marijuana'] = marijuana  # Add all selected marijuana options
            else:
                # No marijuana filter; select all marijuana options by default (omit the clause)
                pass

            if pets:
                query += " AND pets IN ({})".format(','.join(['?'] * len(pets)))
                params['pets'] = pets  # Add all selected pet options
            else:
                # No pets filter; select all pet options by default (omit the clause)
                pass

#            if politics:
 #               query += " AND politics IN ({})".format(','.join(['?'] * len(politics)))
  #              params['politics'] = politics  # Add all selected political views
   #         else:
                # No politics filter; select all political views by default (omit the clause)
    #            pass

            if polyPreference:
                query += " AND poly_preference IN ({})".format(','.join(['?'] * len(polyPreference)))
                params['poly_preference'] = polyPreference  # Add all selected poly preferences
            else:
                # No polyPreference filter; select all preferences by default (omit the clause)
                pass

#            if religion:
 #               query += " AND religion IN ({})".format(','.join(['?'] * len(religion)))
  #              params['religion'] = religion  # Add all selected religions
   #         else:
                # No religion filter; select all religions by default (omit the clause)
    #            pass

            if sexualOrientation:
                query += " AND sexualOrientation IN ({})".format(','.join(['?'] * len(sexualOrientation)))
                params['sexualOrientation'] = sexualOrientation  # Add all selected orientations
            else:
                # No sexualOrientation filter; select all orientations by default (omit the clause)
                pass

            if smoking:
                query += " AND smoking IN ({})".format(','.join(['?'] * len(smoking)))
                params['smoking'] = smoking  # Add all selected smoking preferences
            else:
                # No smoking filter; select all smoking preferences by default (omit the clause)
                pass

            if vaping:
                query += " AND vaping IN ({})".format(','.join(['?'] * len(vaping)))
                params['vaping'] = vaping  # Add all selected vaping preferences
            else:
                # No vaping filter; select all vaping preferences by default (omit the clause)
                pass

            if wantsKids:
                query += " AND wants_kids IN ({})".format(','.join(['?'] * len(wantsKids)))
                params['wants_kids'] = wantsKids  # Add all selected wantsKids options
            else:
                # No wantsKids filter; select all options by default (omit the clause)
                pass

             # Execute query
            print("Final Query:", query)
            print("Parameters:", params)
#            print("height:", min_height)
 #           print("age min:", age_min)
  #          print("age max:", age_max)

            cursor.execute(query, tuple(drinking) + tuple(drugs) + tuple(education) + tuple(ethnicity) + tuple(gender) + tuple(hasKids) + tuple(languages) + tuple(location) + tuple(marijuana) + tuple(pets) + tuple(polyPreference) + tuple(sexualOrientation) + tuple(smoking) + tuple(vaping) + tuple(wantsKids))
            results = cursor.fetchall()
            # Close connection
            conn.close()

  #          print("Matching Profiles:")
   #         for row in results:
    #            print(row)

            for row in results:
                profile = dict(zip([column[0] for column in cursor.description], row))
                profiles.append(profile)

            for profile in profiles:
                if profile['photo']:
                    profile['photo'] = f"data:image/jpeg;base64,{base64.b64encode(profile['photo']).decode('utf-8')}"

            return render_template('search.html', results=results, profiles=profiles, **lists)

        except Exception as e:
            print(f"An error occurred: {e}")
            return render_template('search.html', profiles=profiles, error="An error occurred while fetching profiles.", **lists)

    return render_template('search.html', profiles=profiles, **lists)
