import mysql.connector
import json

# --- 1. SETUP ---
try:
    db = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="Ibrahim@321", 
        database="job_agent"
    )
    cursor = db.cursor(dictionary=True) # Use dictionary cursor
    print("✅ Database connected successfully.")
except mysql.connector.Error as err:
    print(f"❌ DATABASE ERROR: {err}")
    exit()

# --- 2. THE "SMART MATCH" LOGIC ---
def calculate_match_score(job_skills, user_skills):
    """
    Compares job requirements vs user skills and returns a score (0-100)
    and a list of missing skills.
    """
    if not job_skills or not user_skills:
        return 0, []
    
    # Normalize to lowercase for a case-insensitive comparison
    job_set = set(s.lower() for s in job_skills)
    user_set = set(s.lower() for s in user_skills)
    
    if not job_set: # If the job has no required skills, it's a 0% match
        return 0, []

    matches = job_set.intersection(user_set)
    score = int((len(matches) / len(job_set)) * 100)
    
    missing = list(job_set - user_set)
    return score, missing

# --- 3. THE MAIN FUNCTION ---
def find_jobs():
    # 1. Get user input
    user_input = input("\nEnter your skills (comma-separated, e.g. python, docker, aws):\n> ")
    user_skill_list = [skill.strip().lower() for skill in user_input.split(',')]

    print(f"\nSearching for jobs matching: {', '.join(user_skill_list)}")
    
    # 2. Fetch all *processed* jobs from the database
    try:
        cursor.execute("SELECT * FROM job_openings WHERE is_extracted = TRUE")
        all_jobs = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"❌ DB FETCH FAILED: {err}")
        return
        
    if not all_jobs:
        print("No processed jobs found in the database. Run extractor.py first.")
        return

    # 3. Calculate match score for every job
    results = []
    for job in all_jobs:
        # Parse the JSON 'required_skills' from the database
        try:
            job_skills_list = json.loads(job['required_skills']) if job['required_skills'] else []
        except json.JSONDecodeError:
            job_skills_list = [] # Handle bad JSON data if any

        score, missing = calculate_match_score(job_skills_list, user_skill_list)
        
        # We only want to see jobs that are at least a partial match
        if score > 0:
            results.append({
                "id": job['id'],
                "title": job['job_title'],
                "company": job['company'],
                "score": score,
                "missing_skills": ", ".join(missing),
                "url": job['job_url']
            })

    # 4. Sort results by score (best matches first)
    results.sort(key=lambda x: x['score'], reverse=True)

    # 5. Display in a clean text format
    if not results:
        print("No jobs found with those skills. Try a broader search.")
        return

    print("\n--- Your Smart Job Matches ---")
    for job in results:
        print(f"\nScore: {job['score']}%")
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Skills Gap: {job['missing_skills']}")
        print(f"URL: {job['url']}")
        print("-" * 20) # Separator
    
    # 6. Clean up
    cursor.close()
    db.close()

if __name__ == "__main__":
    find_jobs()