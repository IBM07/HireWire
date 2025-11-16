# --- 1. The Imports ---
# We import Flask (the core framework) and key utilities.
# - 'request': An object that holds all incoming data (like URLs, headers).
# - 'jsonify': A function that correctly formats our Python dictionaries into
#              a JSON response that browsers/apps can understand.
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import json

# --- 2. The Application Instance ---
# This 'app' object is the heart of our Flask application.
# '__name__' tells Flask where to find other files (like templates),
# but for an API, it's mostly boilerplate.
app = Flask(__name__)
CORS(app)
# --- 3. The "Interview" Critical Concept: Database Connections ---
# !! DO NOT DO THIS (The Junior Mistake) !!
# db = mysql.connector.connect(...)
# cursor = db.cursor()
#
# Why? A web server handles *many requests at once* (multithreading). If two
# requests try to use the *same* 'cursor' at the *same* time, your app will
# crash or corrupt data.
#
# THE SENIOR SOLUTION:
# You MUST create a *fresh* database connection for *every single API request*
# and close it immediately after. This is thread-safe and stable.
def get_db_connection():
    # This function creates a new, fresh connection every time it's called.
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="Ibrahim@321", 
        database="job_agent"
    )

# --- 4. The "Smart Match" Logic ---
# This is our "business logic." It's good practice to keep this
# separate from the API routing. This code is perfect.
def calculate_match_score(job_skills, user_skills):
    if not job_skills or not user_skills:
        return 0, []
    
    job_set = set(s.lower() for s in job_skills)
    user_set = set(s.lower() for s in user_skills)
    
    if not job_set:
        return 0, []

    matches = job_set.intersection(user_set)
    score = int((len(matches) / len(job_set)) * 100)
    
    missing = list(job_set - user_set)
    return score, missing

# --- 5. The API Endpoints (The "Routes") ---
#
# This is an "endpoint." The '@app.route' is a "decorator."
# It's a special Python feature that "wraps" our function.
# This tells Flask: "If anyone sends a GET request to 'http://.../jobs',
# run the 'search_jobs' function."

@app.route("/jobs", methods=["GET"])
def search_jobs():
    
    # 5a. Get User Input:
    # We use the 'request' object to get query parameters from the URL.
    # e.g., /jobs?skills=python,docker
    # 'request.args.get()' is the standard way to do this.
    skills = request.args.get('skills') # Gets 'python,docker' as a string
    limit = request.args.get('limit', default=50, type=int) # With a default

    # 5b. Database Logic (The "Safe Way"):
    conn = None # Initialize to None
    try:
        # We call our function to get a *fresh* connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM job_openings WHERE is_extracted = TRUE ORDER BY created_at DESC")
        jobs = cursor.fetchall()

    except mysql.connector.Error as err:
        # If the database fails, send a professional 500 error.
        # Don't just let the app crash.
        return jsonify({"error": f"Database Error: {err}"}), 500
    finally:
        if conn:
            conn.close()

    # Business Logic (The Smart Match):
    results = []
    user_skill_list = [s.strip().lower() for s in skills.split(',')] if skills else []

    for job in jobs:
        try:
            job_skills_list = json.loads(job['required_skills']) if job['required_skills'] else []
        except json.JSONDecodeError:
            job_skills_list = []
        
        match_score = 0
        missing_skills = []

        if user_skill_list:
            match_score, missing_skills = calculate_match_score(job_skills_list, user_skill_list)
            if match_score == 0:
                continue

        results.append({
            "id": job['id'],
            "title": job['job_title'],
            "company": job['company'],
            "location": job['location_scraped'],
            "is_remote": bool(job['is_remote']),
            "match_score": f"{match_score}%",
            "skills_missing": missing_skills,
            "apply_url": job['job_url']
        })

    # 5d. Sorting and Filtering:
    if user_skill_list:
        results.sort(key=lambda x: int(x['match_score'].strip('%')), reverse=True)

    # 5e. The Return:
    # We MUST use 'jsonify'.
    # 'jsonify' does two things:
    # 1. Converts our Python dict to a JSON string.
    # 2. Sets the HTTP header 'Content-Type: application/json'
    # An interviewer will know if you just 'return dict' (the junior way).
    return jsonify({"total": len(results), "jobs": results[:limit]})

# --- 6. The "Entry Point" ---
# This 'if' statement means this code only runs
# if you execute this file directly (e.g., 'python api.py').
# 'debug=True' is great for development (it auto-reloads)
# but MUST be 'False' in production.
if __name__ == "__main__":
    app.run(debug=True, port=5000) # We'll run this on port 5000
