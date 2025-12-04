import streamlit as st
import requests
import os
import PyPDF2  # You need to install this: pip install PyPDF2

# --- 1. Configuration & Cloud Readiness ---
# GCP requires dynamic configuration. We read from Environment Variables.
# Locally, it defaults to localhost. On GCP, you set 'API_URL' in the dashboard.
API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:5000")

# --- 2. Caching & API Logic ---
@st.cache_data(ttl=60) # Cache for 1 minute to prevent spamming
def fetch_jobs_from_api(skills_query):
    try:
        # Construct endpoint using the dynamic base URL
        api_url = f"{API_BASE_URL}/jobs"
        params = {"skills": skills_query, "per_page": 50}
        
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def extract_text_from_pdf(pdf_file):
    """Helper feature to read resumes"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception:
        return ""

# --- 3. Page Config ---
st.set_page_config(
    page_title="CareerCortex | AI Job Agent",
    page_icon="🚀",
    layout="wide"
)

# --- 4. Session State Setup ---
# This ensures the input box updates automatically when a resume is uploaded
if 'skills_input' not in st.session_state:
    st.session_state.skills_input = "python, docker, fastapi"

# --- 5. The UI ---
st.title("🚀 CareerCortex")
st.markdown("### The AI Agent that reads your resume and finds your job.")

# --- FEATURE: Resume Uploader ---
with st.expander("📄 Upload Resume (Optional) - Let AI extract your skills", expanded=True):
    uploaded_file = st.file_uploader("Upload PDF Resume", type="pdf")
    if uploaded_file:
        resume_text = extract_text_from_pdf(uploaded_file)
        if resume_text:
            # Simple keyword extraction simulation
            # In a real interview, you'd mention you could use an LLM here
            found_skills = []
            common_tech = [
    # Core Languages
    "python", "java", "c++", "go", "golang", "rust", "javascript", "typescript", "node.js",
    
    # Data Structures & Algorithms
    "arrays", "linked lists", "binary trees", "avl trees", "b-trees", "graphs", 
    "bfs", "dfs", "hash maps", "heaps", "sorting algorithms", "searching algorithms", "big o notation",
    
    # Object-Oriented Programming & Design
    "inheritance", "polymorphism", "encapsulation", "abstraction", "solid principles",
    "singleton pattern", "factory pattern", "observer pattern", "strategy pattern", 
    "decorator pattern", "adapter pattern", "dependency injection",
    
    # Backend Frameworks
    "django", "flask", "fastapi", "tornado", "sanic",
    
    # API Standards & Protocols
    "restful apis", "hateoas", "graphql", "grpc", "protocol buffers", "websockets",
    
    # ORM & Data Validation
    "sqlalchemy", "django orm", "pydantic", "alembic",
    
    # Databases (Relational & NoSQL)
    "postgresql", "mysql", "mariadb", "sqlite", 
    "mongodb", "cassandra", "scylladb", "dynamodb", "neo4j",
    
    # Caching & Search
    "redis", "memcached", "elasticsearch", "solr", "meilisearch",
    
    # Async & Task Queues
    "celery", "redis queue", "dramatiq", "asyncio",
    
    # Web Servers
    "gunicorn", "uvicorn", "hypercorn", "wsgi", "asgi",
    
    # System Architecture
    "monolithic architecture", "microservices", "event-driven architecture", "serverless", "soa",
    "horizontal scaling", "vertical scaling", "load balancing", "nginx", "haproxy", "aws alb", 
    "sharding", "consistent hashing", "cap theorem", "distributed systems", 
    "consensus algorithms", "raft", "paxos", "distributed locking", "idempotency", 
    "event sourcing", "cqrs",
    
    # Infrastructure & DevOps
    "docker", "containerd", "kubernetes", "helm charts", "terraform", "ansible", "pulumi", "cloudformation",
    
    # Cloud Platforms (AWS/GCP/Azure)
    "aws", "gcp", "azure", "ec2", "lambda", "eks", "ecs", "s3", "ebs", "glacier", 
    "vpc", "route53", "cloudfront",
    
    # CI/CD
    "github actions", "gitlab ci", "jenkins", "circleci", "argocd",
    
    # Testing
    "pytest", "unittest", "selenium", "playwright", "postman", "newman", "mocking",
    
    # Tools & Observability
    "git", "gitflow", "bash scripting", "zsh", "grep", "sed", "awk", "ssh", "curl", 
    "prometheus", "grafana", "elk stack", "jaeger", "zipkin", "sentry",
    
    # Security
    "owasp top 10", "oauth2", "jwt", "openid connect", "tls/ssl",
    
    # Data Engineering & AI Integration
    "apache kafka", "rabbitmq", "airflow", "spark", "etl pipelines",
    "langchain", "vector databases", "pinecone", "milvus", "openai api", "huggingface transformers"
]
            
            for tech in common_tech:
                if tech in resume_text.lower():
                    found_skills.append(tech)
            
            if found_skills:
                # Update the session state to auto-fill the input box
                st.session_state.skills_input = ", ".join(found_skills)
                st.success(f"✅ Extracted {len(found_skills)} skills from your resume!")
            else:
                st.warning("Could not identify specific tech skills, but file loaded.")

# --- Main Search Input ---
# We bind the value to session_state so the resume uploader can update it
user_skills = st.text_input(
    "Your Skills",
    key="skills_input", # This links the input to our variable
    help="Enter skills comma-separated, or upload resume above."
)

if st.button("Find My Match", type="primary"):
    if not user_skills:
        st.error("Please enter skills or upload a resume.")
    else:
        with st.spinner(f"Connecting to AI Agent at {API_BASE_URL}..."):
            data = fetch_jobs_from_api(user_skills)

        if "error" in data:
            st.error(f"❌ Connection Failed: {data['error']}")
            st.info("💡 If running locally, ensure backend is on port 5000.")
            st.info("💡 If on GCP, ensure API_URL environment variable is set.")
        else:
            # Handle Pagination Structure
            total_count = data.get('pagination', {}).get('total_jobs', 0)
            jobs = data.get('jobs', [])

            if not jobs:
                st.warning("No jobs found. Try broader keywords.")
            else:
                st.success(f"🎯 Found {total_count} perfect matches based on your profile.")
                
                # Display Grid
                for job in jobs:
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.subheader(job['title'])
                            st.caption(f"{job['company']} | {job['location']} | {'Remote 🌍' if job.get('is_remote') else 'On-site 🏢'}")
                            if job.get('skills_missing'):
                                st.markdown(f"⚠️ **Missing:** `{', '.join(job['skills_missing'][:5])}`")
                        with c2:
                            st.metric("Match Score", job['match_score'])
                            st.link_button("Apply Now", job.get('apply_url', '#'))

# --- Footer for Interview Credit ---
st.markdown("---")
st.caption("Powered by Custom Python Scraper, Flask API, and Streamlit Frontend.")