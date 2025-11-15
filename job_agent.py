from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import time
import urllib.parse 
import mysql.connector


# Connecting to the Database!
try:
    db = mysql.connector.connect(
        host="127.0.0.1",
        user="root", 
        password="Ibrahim@321", 
        database="job_agent"
    )
    cursor = db.cursor()
    print("✅ Database connected successfully.")
except mysql.connector.Error as err:
    print(f"❌ DATABASE ERROR: {err}")
    print("Please ensure MySQL is running and credentials are correct.")
    exit() # Exit the script if DB connection fails

def get_user_input(prompt, valid_options=None):
    """
    A helper function to get comma-separated input from the user.
    If valid_options is provided, it filters the user's input.
    """
    print(f"\n{prompt}")
    if valid_options:
        print(f"(Options: {', '.join(valid_options)})")
    
    user_input = input("> ").strip().lower()
    
    if not user_input:
        return [] # Return an empty list if the user just hits Enter

    # Split the input by comma and strip whitespace
    items = [item.strip() for item in user_input.split(',')]
    
    # If we have a list of valid options, filter the user's list
    if valid_options:
        filtered_items = [item for item in items if item in valid_options]
        invalid_items = [item for item in items if item not in valid_options]
        
        if invalid_items:
            print(f"Ignoring invalid options: {', '.join(invalid_items)}")
        return filtered_items
        
    return items

# Main Functions! 
def scrape():
    """
    An interactive web scraper that finds job listings on remote.com
    based on user input.
    """
    
    # --- 1. Get User Input ---
    
    # Simple text input
    search_term = input("Enter job title (or press Enter to skip):\n> ").strip()
    country_code = input("\nEnter 3-letter country code (e.g., IND, USA, or press Enter to skip):\n> ").strip().upper()

    # List-based inputs
    employment_types = get_user_input(
        "Enter employment types (comma-separated, or press Enter to skip):",
        valid_options=["full_time", "part_time", "contractor"]
    )
    
    locations = get_user_input(
        "Enter workplace locations (comma-separated, or press Enter to skip):",
        valid_options=["remote", "hybrid", "on_site"]
    )
    
    seniorities = get_user_input(
        "Enter seniority levels (comma-separated, or press Enter to skip):",
        valid_options=["entry_level", "mid_level", "senior", "manager", "director", "executive"]
    )

    # --- 2. Build the URL ---
    base_url = "https://remote.com/jobs/all"
    
    # This dictionary will hold all our query parameters
    
    params = {
    
    }
    
    # Add parameters *only if* the user provided them
    if search_term:
        params['query'] = search_term
    if country_code:
        params['country'] = country_code
    if employment_types:
        params['employmentType'] = employment_types # Pass the whole list
    if locations:
        params['workplaceLocation'] = locations # Pass the whole list
    if seniorities:
        params['seniority'] = seniorities # Pass the whole list
    
    # urlencode handles lists by creating repeated keys (e.g., &seniority=...&seniority=...)
    query_string = urllib.parse.urlencode(params, doseq=True)
    url_jobs = f"{base_url}?{query_string}"
    
    print(f"\n--- Starting scraper for URL: {url_jobs} ---")

    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    # Job Title and It's Link!
    driver.get(url_jobs)

    soup_list_page = BeautifulSoup(driver.page_source, "html.parser")
    job_links = soup_list_page.find_all("a", class_=re.compile(r"sc-90158e63-0.*sc-31ccc88a-0"))

    for link in job_links:
        full_job_url = "https://remote.com" + link["href"]
        job_title = link.get_text(strip=True)
        print(job_title, full_job_url)
        driver.get(full_job_url)
        soup_desc_page = BeautifulSoup(driver.page_source, "html.parser")
        time.sleep(2)
        if soup_desc_page.body:
            raw_text_all = soup_desc_page.body.get_text(separator=' ', strip=True)
            try:
                sql = """
                INSERT INTO job_openings 
                (search_query, job_url, job_title, raw_description) 
                VALUES (%s, %s, %s, %s)
                """
                # Use search_term (from user input) as the search_query
                vals = (search_term, full_job_url, job_title, raw_text_all)
                
                cursor.execute(sql, vals)
                db.commit() # Commit the change to the database
                
                print(f"✅ SAVED: {job_title}")
                
            except mysql.connector.Error as err:
                if err.errno == 1062: # Error code for "Duplicate entry"
                    print(f"⚪️ SKIPPED (Duplicate): {job_title}")
                else:
                    print(f"❌ DATABASE ERROR: {err}")
                    db.rollback() # Roll back changes on error
        else:
            print("Not Found!")

    driver.quit()
    print("Scraping Done!")

    cursor.close()
    db.close()
    print("✅ Database connection closed.")

if __name__ == "__main__":
    scrape()