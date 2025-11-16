import streamlit as st
import requests

@st.cache_data
def fetch_jobs_from_api(skills_query):
    """
    Calls our Flask API to get job data.
    This function will only re-run if 'skills_query' changes.
    """
    try:
        api_url = "http://127.0.0.1:5000/jobs"
        params = {"skills": skills_query}
        
        response = requests.get(api_url, params=params)
        
        response.raise_for_status() 
        
        return response.json()
        
    except requests.exceptions.ConnectionError:
        return {"error": "ConnectionError"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTPError: {e}"}

st.set_page_config(
    page_title="CareerCortex",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 CareerCortex")
st.write("Enter your skills. Our AI will find the jobs that *actually* match.")

user_skills = st.text_input(
    "Your Skills",
    "python, docker, fastapi",
    help="Enter your skills, comma-separated."
)

if st.button("Find My Match"):

    if not user_skills:
        st.error("Please enter at least one skill to start.")
    else:
        with st.spinner(f"Analyzing jobs for '{user_skills}'..."):
            data = fetch_jobs_from_api(user_skills)

        if "error" in data:
            if data["error"] == "ConnectionError":
                st.error("Fatal Error: Cannot connect to the backend API.")
                st.info("Is your 'api.py' server running in a separate terminal?")
            else:
                st.error(f"An API error occurred: {data['error']}")
        
        else:
            jobs = data.get('jobs', [])
            
            if not jobs:
                st.warning("No jobs found matching your skills. Try being less specific.")
            else:
                st.success(f"Found {data['total']} matching jobs!")
                
                for job in jobs:
                    with st.container(border=True): 
                        
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.subheader(f"**{job['title']}**")
                            st.caption(f"{job['company']}  •  {job['location']}  •  Remote: {'✅ Yes' if job['is_remote'] else '❌ No'}")
                            
                            if job['skills_missing']:
                                st.error(f"**Skills Gap:** {', '.join(job['skills_missing'])}")
                        
                        with col2:
                            st.markdown(f"### {job['match_score']}")
                            st.link_button("Apply Now ↗", job['apply_url'])
