import mysql.connector
import ollama
import json

# Connecting to the Database!
try:
    db = mysql.connector.connect(
        host="127.0.0.1",
        user="root", 
        password="Ibrahim@321", 
        database="job_agent"
    )
    cursor = db.cursor(dictionary=True)
    print("✅ Database connected successfully.")
except mysql.connector.Error as err:
    print(f"❌ DATABASE ERROR: {err}")
    print("Please ensure MySQL is running and credentials are correct.")
    exit() # Exit the script if DB connection fails

# Connecting to Ollama
try:
    ollama.list() # Test connection
    print("✅ Ollama connection successful.")
except Exception as e:
    print(f"❌ OLLAMA ERROR: {e}")
    print("Please ensure Ollama is running.")
    exit()

# --- 2. THE EXTRACTION PROMPT (THE "BRAIN") ---
# This is the most important part. It's a precise instruction for the AI.
extraction_prompt = """
You are an expert, deterministic data extraction agent. You will be given the full raw text of a job posting. Your only task is to return a single valid, minified JSON object with the exact keys below and nothing else. Do not write any explanation, commentary, or extra characters. Use the exact key names, value types, order, and fallback rules described. The final JSON must validate: company (string), location_scraped (string), is_remote (boolean), job_type (string), seniority (string), required_skills (array of strings). Return fields in this exact order.
REQUIRED OUTPUT SCHEMA (exact keys, types, and rules)
- company: string
- If company name is not present, use "Not specified". Trim whitespace and remove surrounding punctuation.
- location_scraped: string
- Primary location or locations separated by " + " when multiple (e.g., "Latin America + 2 more").
- If only "Remote" or "Anywhere" appears and no country/city given, use "Remote".
- If both remote and specific locations appear, format exactly: "Remote + [locations]" (e.g., "Remote + USA").
- If no location present, use "Not specified".
- is_remote: boolean
- true if the posting explicitly says Remote, Work from Home, Hybrid, Anywhere, or close synonyms. false otherwise.
- job_type: string
- One of: "Full-time", "Part-time", "Contract", "Contractor", "Temporary", "Internship", "Freelance", or a short custom label from the posting. If absent, use "Not specified".
- seniority: string
- One concise label such as "Entry-level", "Junior", "Mid-level", "Senior", "Lead", or a short phrase from the posting. If using a phrase, trim to maximum 60 characters (cut off at 60 characters with no ellipsis). If absent, use "Not specified".
- required_skills: array of strings (JSON list)
- List every explicit technology, programming language, platform, analytics tool, database, cloud, framework, or engineering tool mentioned. Normalize each skill to a concise canonical form only when the text explicitly matches a canonical variant (see normalization examples). Do not invent skills. Exclude soft skills like communication, leadership, or teamwork.
- Deduplicate case-insensitively, then sort alphabetically (A→Z) in the JSON output.
- If none present, return an empty array [] (NOT the string "Not specified").
GENERAL RULES (must follow strictly)
- Return EXACTLY one minified JSON object and nothing else (single line, no newlines, no code fences).
- Use boolean true/false for is_remote (lowercase).
- required_skills must always be a JSON array. If no skills, return [] (empty array).
- When canonicalizing, preserve common capitalization for acronyms (SQL, AWS, GCP, GA4, GTM, UI) and product names (PowerBI, BigQuery, Redshift, Looker Studio). For languages use standard names: Python, JavaScript, Java, C, C++, Ruby, Go, R.
- Do not invent or infer skills not explicitly present. Minor variants should be normalized only when they clearly match (e.g., "Postgres" → "PostgreSQL").
- If the posting includes lists, bullets, headings (Qualifications/Requirements), or inline mentions, extract all explicit tools named.
- If you cannot determine company/location/job_type/seniority, use "Not specified" exactly as the string value.
- Always output fields in the order: company, location_scraped, is_remote, job_type, seniority, required_skills.
- Validate the JSON: company and location_scraped are strings, is_remote boolean, job_type and seniority strings, required_skills an array of strings.
NORMALIZATION EXAMPLES
- "Google Analytics 4" or "Google Analytics" → "GA4" if explicitly versioned or written GA4; otherwise keep "Google Analytics".
- "Power BI" → "PowerBI"
- "Amazon Web Services" → "AWS"
- "Google Cloud Platform" → "GCP"
- "Postgres", "PostgreSQL" → "PostgreSQL"
- "Big Query", "BigQuery" → "BigQuery"
- "Airflow", "Apache Airflow" → "Apache Airflow"
- "Looker Studio" → "Looker Studio"
EXAMPLES (single-line expected output) Input fragment: "Utilize SQL, Python, BigQuery and PowerBI to deliver scalable insights."
Output: {"company":"Not specified","location_scraped":"Not specified","is_remote":false,"job_type":"Not specified","seniority":"Not specified","required_skills":["BigQuery","PowerBI","Python","SQL"]}
Input fragment: "Remote. Full-time. Hands-on experience with GA4, GTM and Looker Studio is required."
Output: {"company":"Not specified","location_scraped":"Remote","is_remote":true,"job_type":"Full-time","seniority":"Not specified","required_skills":["GA4","GTM","Looker Studio"]}
FALLBACK & VALIDATION RULES
- If required_skills parses to empty but the text clearly contains known skill tokens from the normalization list, include those tokens. Use a literal match (word-boundary) to decide.
- If a posting contains a "Qualifications" or "Requirements" section, prioritize it for skills extraction.
- Ensure final JSON validates against the schema above. If any validation would fail, return "Not specified" for that field (except required_skills which must be []).
STRICT FORMATTING REMINDER Return only the JSON object and nothing else. Single-line, minified, example valid output: {"company":"Colibri Group","location_scraped":"Remote","is_remote":true,"job_type":"Full-time","seniority":"Not specified","required_skills":["BigQuery","GA4","GTM","PowerBI","Python","Redshift","SQL"]}
End of system instructions.

"""

def extract_data(raw_text):
    """
    Uses Ollama to extract structured data from raw text.
    """
    try:
        response = ollama.chat(
            model='llama3:8b', # Our recommended model
            messages=[
                {'role': 'system', 'content': extraction_prompt},
                {'role': 'user', 'content': raw_text}
            ],
            options={'temperature': 0.0}, # We want 100% consistent, non-creative answers
            format='json' # This forces llama3 to output valid JSON
        )
        
        # 'response' contains the JSON string
        json_data_string = response['message']['content']
        
        # Convert the JSON string into a Python dictionary
        data_dict = json.loads(json_data_string)
        return data_dict

    except Exception as e:
        print(f"❌ LLM EXTRACTION FAILED: {e}")
        return None

# --- 3. THE MAIN PROCESSING LOOP ---
def main():
    print("\nStarting extraction process...")
    
    # Find all jobs that have NOT been processed yet (seniority and required_skills is our marker)
    cursor.execute("SELECT id, raw_description FROM job_openings WHERE is_extracted = FALSE;")
    jobs_to_process = cursor.fetchall()
    
    if not jobs_to_process:
        print("No new jobs to process. Exiting.")
        return

    print(f"Found {len(jobs_to_process)} jobs to process.")
    
    for job in jobs_to_process:
        job_id = job["id"]
        raw_text = job['raw_description']
        
        print(f"\n--- Processing Job ID: {job_id} ---")
        
        # 1. Get the structured data from the LLM
        structured_data = extract_data(raw_text)
        
        if structured_data:
            print(f"   Extracted: {structured_data}")
            
            # 2. Update the database with the new data
            try:
                skills_list = structured_data.get('required_skills', [])
                skills_json = json.dumps(skills_list) # e.g., '["Python", "Docker"]
                sql = """
                UPDATE job_openings 
                SET 
                    company = %s,
                    location_scraped = %s,
                    is_remote = %s,
                    job_type = %s,
                    seniority = %s,
                    required_skills = %s,
                    is_extracted = TRUE
                WHERE id = %s
                """
                vals = (
                    structured_data.get('company', 'Not specified'),
                    structured_data.get('location_scraped', 'Not specified'),
                    structured_data.get('is_remote'), # Gets bool or None
                    structured_data.get('job_type', 'Not specified'),
                    structured_data.get('seniority', 'Not specified'),
                    skills_json,
                    job_id
                )
                
                cursor.execute(sql, vals)
                db.commit()
                print(f"✅ Job ID {job_id} updated.")
                
            except mysql.connector.Error as err:
                print(f"❌ DB UPDATE FAILED: {err}")
                db.rollback()
        else:
            print(f"⚠️ Skipped Job ID {job_id} due to extraction error.")

    cursor.close()
    db.close()
    print("✅ Database connection closed.")

if __name__ == "__main__":
    main()