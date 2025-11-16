from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import json

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="Ibrahim@321", 
        database="job_agent"
    )

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

@app.route("/jobs", methods=["GET"])
def search_jobs():
    
    skills = request.args.get('skills')
    limit = request.args.get('limit', default=50, type=int)

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM job_openings WHERE is_extracted = TRUE ORDER BY created_at DESC")
        jobs = cursor.fetchall()

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database Error: {err}"}), 500
    finally:
        if conn:
            conn.close()

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

    if user_skill_list:
        results.sort(key=lambda x: int(x['match_score'].strip('%')), reverse=True)

    return jsonify({"total": len(results), "jobs": results[:limit]})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
