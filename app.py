# --- 1. The Imports ---
# 'streamlit' is the core library, we conventionall import it as 'st'.
# 'requests' is the library we use to *call* our Flask API.
# This frontend is "dumb" - it holds no logic, it just asks the backend.
import streamlit as st
import requests

# --- 2. The "Interview" Critical Concept: Caching ---
#
# !! The Junior Mistake !!
# Calling 'requests.get()' *directly* inside the 'if st.button' block.
# Why? If the user interacts with *another* widget (imagine a slider),
# the script reruns, and it would *call your API again* needlessly.
#
# THE SENIOR SOLUTION:
# We wrap our API call in a Streamlit "cache" function.
# '@st.cache_data' is a decorator that tells Streamlit:
# "Before running this function, check if it has been run with these *exact
# arguments* before. If yes, return the saved result immediately without
# running the function."
# This is your #1 performance tool.
@st.cache_data  # <-- This is the magic decorator
def fetch_jobs_from_api(skills_query):
    """
    Calls our Flask API to get job data.
    This function will only re-run if 'skills_query' changes.
    """
    try:
        # We call our Flask API, which is running on port 5000
        api_url = "http://127.0.0.1:5000/jobs"
        params = {"skills": skills_query}
        
        response = requests.get(api_url, params=params)
        
        # Raise an error if the API call failed (e.g., 500 error)
        response.raise_for_status() 
        
        return response.json()  # Return the clean JSON data
        
    except requests.exceptions.ConnectionError:
        # This catches the error if 'api.py' isn't running
        return {"error": "ConnectionError"}
    except requests.exceptions.HTTPError as e:
        # This catches errors from our API (like 500)
        return {"error": f"HTTPError: {e}"}

# --- 3. The Page Configuration ---
# This MUST be the first Streamlit command you run.
# It sets the browser tab title, icon, and layout.
# 'layout="wide"' gives us more space to work with.
st.set_page_config(
    page_title="CareerCortex",
    page_icon="🚀",
    layout="wide"
)

# --- 4. The UI (The "Script" Part) ---
# Streamlit runs this like a script. It just draws
# components from top to bottom.
st.title("🚀 CareerCortex")
st.write("Enter your skills. Our AI will find the jobs that *actually* match.")

# 'st.text_input' creates a text box.
# The variable 'user_skills' will hold whatever the user types.
user_skills = st.text_input(
    "Your Skills",
    "python, docker, fastapi",  # This is the default text
    help="Enter your skills, comma-separated."
)

# 'st.button' creates a button.
# The code *inside* this 'if' block only runs when the button is clicked.
if st.button("Find My Match"):

    # 4a. Input Validation:
    if not user_skills:
        st.error("Please enter at least one skill to start.")
    else:
        # 4b. Call our *cached* function
        # 'st.spinner' shows a nice loading message
        with st.spinner(f"Analyzing jobs for '{user_skills}'..."):
            data = fetch_jobs_from_api(user_skills)

        # 4c. Handle API Errors:
        if "error" in data:
            if data["error"] == "ConnectionError":
                st.error("Fatal Error: Cannot connect to the backend API.")
                st.info("Is your 'api.py' server running in a separate terminal?")
            else:
                st.error(f"An API error occurred: {data['error']}")
        
        # 4d. Display Results:
        else:
            jobs = data.get('jobs', [])
            
            if not jobs:
                st.warning("No jobs found matching your skills. Try being less specific.")
            else:
                st.success(f"Found {data['total']} matching jobs!")
                
                # Loop through the JSON results from our API
                for job in jobs:
                    # 'st.container' creates a visual "card" for each job
                    with st.container(border=True): 
                        
                        # 'st.columns' creates a grid. [3, 1] means the
                        # first column is 3x wider than the second.
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.subheader(f"**{job['title']}**")
                            st.caption(f"{job['company']}  •  {job['location']}  •  Remote: {'✅ Yes' if job['is_remote'] else '❌ No'}")
                            
                            if job['skills_missing']:
                                # 'st.error' is a great way to highlight the "Skills Gap"
                                st.error(f"**Skills Gap:** {', '.join(job['skills_missing'])}")
                        
                        with col2:
                            # Use markdown to make the score big and bold
                            st.markdown(f"### {job['match_score']}")
                            # 'st.link_button' creates a real hyperlink
                            st.link_button("Apply Now ↗", job['apply_url'])