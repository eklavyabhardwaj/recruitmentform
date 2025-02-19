from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
import requests
import pandas as pd
import random
import os
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = str(random.randint(1000000000000000, 9999999999999999))

# ----------------------------------------------------------------
#  ERP Configuration
# ----------------------------------------------------------------
BASE_URL = 'https://erpv14.electrolabgroup.com/'
JOB_OPENING_ENDPOINT = 'api/resource/Job Opening'
JOB_APPLICANT_ENDPOINT = 'api/resource/Job Applicant'

AUTH_HEADERS = {
    'Authorization': 'token 3ee8d03949516d0:6baa361266cf807',
    'Content-Type': 'application/json'
}

# Folder for saving uploaded resumes
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Resume Attachments')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed file extensions for resume upload
ALLOWED_EXTENSIONS = {'pdf'}

# ----------------------------------------------------------------
#  Custom Secure Filename Function
# ----------------------------------------------------------------
def custom_secure_filename(filename):
    """
    This function is similar to Werkzeug's secure_filename,
    but it allows the "@" character to remain.
    """
    # Remove leading/trailing whitespace and replace spaces with underscores
    filename = filename.strip().replace(" ", "_")
    # Allow letters, digits, underscores, hyphens, dots, and the "@" symbol
    return re.sub(r'(?u)[^-\w.@]', '', filename)

# ----------------------------------------------------------------
#  Utility Functions
# ----------------------------------------------------------------

def fetch_job_list():
    """ Fetch all open job openings from ERP. """
    url = BASE_URL + JOB_OPENING_ENDPOINT
    params = {
        'fields': '["name","designation","status","territory","qualification"]',
        'limit_start': 0,
        'limit_page_length': 999999999
    }
    try:
        resp = requests.get(url, headers=AUTH_HEADERS, params=params)
        if resp.status_code == 200:
            data = resp.json()
            df = pd.DataFrame(data.get('data', []))
            if not df.empty and 'status' in df.columns:
                # Filter only open positions
                df = df[df['status'] == 'Open']
                return df.to_dict(orient='records')
    except Exception as e:
        print("Error fetching job list:", e)
    return []

def fetch_job_details(job_id):
    """ Fetch details for one job opening from ERP. """
    url = f"{BASE_URL}{JOB_OPENING_ENDPOINT}/{job_id}"
    params = {
        'fields': '["name","description","custom_no_of_vacancy","territory","designation","qualification"]'
    }
    try:
        resp = requests.get(url, headers=AUTH_HEADERS, params=params)
        if resp.status_code == 200:
            data = resp.json()
            if 'data' in data:
                return data['data']
    except Exception as e:
        print("Error fetching job details:", e)
    return None

# ----------------------------------------------------------------
#  Routes
# ----------------------------------------------------------------

@app.route('/')
def job_list():
    """ Landing Page: Displays a list of open jobs. """
    search_query = request.args.get('search', '').strip().lower()
    qualification_filter = request.args.get('qualification', '').strip()
    location_filter = request.args.get('location', '').strip()

    jobs = fetch_job_list()

    qualification_options = sorted({job.get('designation', '') for job in jobs if job.get('designation', '')})
    location_options = sorted({job.get('territory', '') for job in jobs if job.get('territory', '')})

    filtered_jobs = []
    for job in jobs:
        if search_query:
            if (search_query not in job.get('name', '').lower() and
                search_query not in job.get('designation', '').lower()):
                continue
        if qualification_filter and (job.get('designation', '') != qualification_filter):
            continue
        if location_filter and (job.get('territory', '') != location_filter):
            continue
        filtered_jobs.append(job)

    return render_template('job_list.html',
                           jobs=filtered_jobs,
                           qualification_options=qualification_options,
                           locations=location_options,
                           search=search_query,
                           qualification=qualification_filter,
                           location=location_filter)

@app.route('/job/<job_id>')
def job_details(job_id):
    """ Job Details Page: Renders details for a single job. """
    job = fetch_job_details(job_id)
    if not job:
        abort(404, description="Job not found")
    return render_template('job_details.html', job=job)

@app.route('/apply')
def apply():
    """ Application Form Page. """
    job_title = request.args.get('job_title', '')
    designation = request.args.get('designation', '')
    return render_template('index.html', job_title=job_title, designation=designation)

@app.route('/submit', methods=['POST'])
def submit():
    """ Handles the submission of the job application form. """
    try:
        # Retrieve form data
        applicant_name = request.form.get('applicant_name')
        job_title = request.form.get('job_title')
        email_id = request.form.get('email_id')
        designation = request.form.get('designation')
        phone_number = request.form.get('phone_number')
        country = request.form.get('country')
        cover_letter = request.form.get('cover_letter')
        lower_range = request.form.get('lower_range')
        upper_range = request.form.get('upper_range')
        resume_link = request.form.get('resume_link')
        source = request.form.get('source')

        # Handle resume file upload and rename to the applicant's email address using our custom function
        filename = None
        if 'resume_attachment' in request.files:
            resume_file = request.files['resume_attachment']
            if resume_file and resume_file.filename:
                # Check if file extension is allowed
                if '.' in resume_file.filename and resume_file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
                    # Use the email address from the form to create a new filename that retains the "@" character
                    new_filename = custom_secure_filename(email_id) + ".pdf"
                    file_path = os.path.join(UPLOAD_FOLDER, new_filename)
                    resume_file.save(file_path)
                    filename = new_filename
                else:
                    flash("Invalid file format! Please upload a PDF.", "error")
                    return redirect(url_for('apply'))

        # Build payload for ERP API
        data_payload = {
            "applicant_name": applicant_name,
            "job_title": job_title,
            "email_id": email_id,
            "designation": designation,
            "phone_number": phone_number,
            "country": country,
            "source": source,
            "cover_letter": cover_letter,
            "lower_range": lower_range,
            "upper_range": upper_range,
            "resume_attachment": filename if filename else "",
            "resume_link": resume_link
        }

        # Send data to ERP system
        resp = requests.post(BASE_URL + JOB_APPLICANT_ENDPOINT, json=data_payload, headers=AUTH_HEADERS)
        if resp.status_code == 200:
            flash('Form submitted successfully!', 'success')
            return redirect(url_for('apply'))  # Stay on the page to show message
        else:
            flash(f"Error: {resp.status_code} - {resp.text}", 'error')

    except Exception as e:
        flash(f"Error occurred: {str(e)}", 'error')

    return redirect(url_for('apply'))

@app.route('/terms')
def terms():
    """ Terms & Conditions Page. """
    return render_template('tnc.html')

# ----------------------------------------------------------------
#  Main
# ----------------------------------------------------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
    #Pass