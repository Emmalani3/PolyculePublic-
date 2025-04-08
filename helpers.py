import requests

from cs50 import SQL
from flask import redirect, render_template, session
from functools import wraps
from typing import List, Dict


db = SQL("sqlite:///polycule.db")

def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_CLID") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def get_profile_lists():
    education = ["High School Diploma", "Equivalent", "Associate Degree", "Bachelor's Degree", "Master's Degree", "Doctoral Degree", "Post-Doctoral Studies", "Trade School", "Other"]
    ethnicity = ["White", "African/Black", "Asian", "Hispanic/Latino", "European", "Indigenous Peoples", "Middle Eastern", "Native American", "Pacific Islander", "Other"]
    gender = ["Male", "Female", "Agender", "Androgenous", "Bi-gender", "Gender fluid", "Gender queer", "Gender nonconforming", "Inter-sex", "Nonbinary", "Pangender", "Trans Woman", "Trans Man", "Other"]
    hasKids=["Yes", "No"]
    languages =["English","Spanish","Mandarin Chinese","Hindi","French","Arabic","Bengali","Russian","Portuguese","Urdu","German","Japanese","Korean","Italian","Turkish","Vietnamese","Tamil","Polish","Dutch","Persian (Farsi)","Swahili","Malay/Indonesian","Tagalog","Thai","Punjabi","Gujarati","Hebrew","Greek","Ukrainian","Czech","Other"]
    location = ["Sommerset, MA", "Seattle, WA", "Los Angles, CA", "Portland, OR", "Durham, NC", "Raleigh, NC", "New York City, NY"]
    multipleChoice= ["Yes", "No", "Sometimes"]
    orientation = ["Aromantic", "Asexual", "Bisexual", "Bicurious", "Demisexual", "Gay", "Hetroflexible", "Heterosexual", "Homosexual", "Lesbian", "Multisexual", "Omnisexual", "Pansexual", "Queer", "Straight", "Other", "Uncertain"]
    pets=["Dogs", "Cats", "Fish", "Birds", "Hamsters", "Guinea Pigs", "Rabbits", "Reptiles", "Ferrets", "Horses", "Small rodents", "Exotic pets", "Other", "None"]
    polyPreference = ["Ethical Non-Monogamy", "Hirearchy", "Kitchen table poly","New to poly", "Non-Hirerarchy", "Parallel Poly", "Polyfidelity", "Quad", "Relationship Anarchy", "Solo-poly", "Swinger", "Triad", "Other", "Uncertain"]
    pronouns = ["She/ Her", "He/ him", "They/ Them", "Other"]
    religion=["Christianity", "Catholic", "Protestant", "Orthodox", "Islam", "Sunni", "Shia", "Judaism", "Orthodox", "Hinduism", "Buddhism", "Sikhism", "Atheism/Agnosticism", "Spiritual but Not Religious", "Taoism", "Shinto", "Zoroastrianism", "Jainism", "Paganism", "Wicca", "Other Religions", "Other"]
    wantsKids=["Yes", "No", "Okay if you have kids", "Uncertain"]
    yn =["Yes", "No"]
    return {
        "education": education,
        "ethnicity": ethnicity,
        "gender": gender,
        "hasKids": hasKids,
        "languages": languages,
        "location": location,
        "multipleChoice": multipleChoice,
        "orientation": orientation,
        "pets": pets,
        "polyPreference": polyPreference,
        "pronouns": pronouns,
        "religion": religion,
        "wantsKids": wantsKids,
        "yn": yn
    }

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def connect_to_db(db_name: str):
    """Connect to the SQLite database."""
    connection = sqlite3.connect(db_name)
    connection.row_factory = sqlite3.Row  # Access rows as dictionaries
    return connection

def search_users(
    db_name: str,
    search_criteria: Dict[str, str],
    visible_only: bool = True
) -> List[Dict]:
    """
    Search for users based on specific answers in the profile table.
    """
    conn = connect_to_db(db_name)
    cursor = conn.cursor()

    query = """
    SELECT
    user.username,
    profile.DisplayName,
    profile.Biography,
    profile.Photo,
    profile.Gender,
    profile.Location,
    profile.SexualOrientation,
    profile.PolyPreference
FROM profile
JOIN user ON profile.users_CLID = user.CLID
WHERE 1=1
    """
    if visible_only:
        query += " AND profile.visibility_on_search = 1"

    for key in search_criteria:
        query += f" AND {key} = ?"

    try:
        cursor.execute(query, tuple(search_criteria.values()))
        results = cursor.fetchall()
        return [dict(row) for row in results]
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return []
    finally:
        conn.close()
