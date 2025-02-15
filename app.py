from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import requests
import pandas as pd
import random
import os
import re
from werkzeug.utils import secure_filename

random_number_hr = random.randint(1068468484867187618761871687171, 9868468484867187618761871687171)

app = Flask(__name__)
app.secret_key = str(random_number_hr)

base_url = 'https://erpv14.electrolabgroup.com/'
endpoint = 'api/resource/Job Applicant'
url = base_url + endpoint

headers = {
    'Authorization': 'token 3ee8d03949516d0:6baa361266cf807',
    'Content-Type': 'application/json'
}

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Resume Attachments')

@app.route('/get_job_titles', methods=['GET'])
def get_job_titles():
    base_url = 'https://erpv14.electrolabgroup.com/'
    endpoint = 'api/resource/Job Opening'
    url = base_url + endpoint

    params = {
        'fields': '["name","designation","status"]',
        'limit_start': 0, 
        'limit_page_length': 100000000000,
    }

    headers = {
        'Authorization': 'token 3ee8d03949516d0:6baa361266cf807'
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['data'])
            # Only proceed if 'status' column exists
            if 'status' in df.columns:
                df = df[df['status'] == 'Open']
                df.rename(columns={'name': 'job_title'}, inplace=True)
                final_df = df.drop_duplicates(subset='job_title', keep='first')
                job_title_designation = final_df[['job_title', 'designation']].dropna().to_dict(orient='records')
                return jsonify(job_title_designation)
        return jsonify({"error": "Failed to fetch data from API"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_form():
    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        random_number = random.randint(100000, 999999)
        applicant_name = request.form['applicant_name']
        job_title = request.form['job_title']
        email_id = request.form['email_id']
        designation = request.form['designation']
        phone_number = request.form['phone_number']
        status = request.form['status']
        country = request.form['country']
        cover_letter = request.form['cover_letter']
        lower_range = request.form['lower_range']
        upper_range = request.form['upper_range']
        resume_link = request.form['resume_link']

        filename = None
        if 'resume_attachment' in request.files:
            resume_file = request.files['resume_attachment']
            if resume_file and resume_file.filename:
                # Get file extension
                file_extension = os.path.splitext(resume_file.filename)[1]
                # Create temporary filename
                temp_filename = f"resume_{random_number}{file_extension}"
                temp_filepath = os.path.join(UPLOAD_FOLDER, temp_filename)
                
                # Save the file with temporary name
                resume_file.save(temp_filepath)
                filename = temp_filename

        # Prepare work experience data
        work_experience_data = []
        company_names = request.form.getlist('company_name[]')
        for i in range(len(company_names)):
            work_experience_data.append({
                "company_name": request.form.getlist('company_name[]')[i],
                "designation": request.form.getlist('designation[]')[i],
                "salary": request.form.getlist('salary[]')[i],
                "address": request.form.getlist('address[]')[i],
                "contact": request.form.getlist('contact[]')[i],
                "custom_from": request.form.getlist('custom_from[]')[i],
                "custom_to": request.form.getlist('custom_to[]')[i],
                "total_experience": request.form.getlist('total_experience[]')[i]
            })

        # Prepare academic data
        academic_data = []
        school_univs = request.form.getlist('school_univ[]')
        for i in range(len(school_univs)):
            academic_data.append({
                "school_univ": request.form.getlist('school_univ[]')[i],
                "qualification": request.form.getlist('qualification[]')[i],
                "level": request.form.getlist('level[]')[i],
                "year_of_passing": request.form.getlist('year_of_passing[]')[i],
                "class_per": request.form.getlist('class_per[]')[i],
                "maj_opt_subj": request.form.getlist('maj_opt_subj[]')[i]
            })

        # Prepare the final payload
        form_data = {
            "applicant_name": applicant_name,
            "job_title": job_title,
            "email_id": email_id,
            "designation": designation,
            "phone_number": phone_number,
            "status": status,
            "country": country,
            "cover_letter": cover_letter,
            "lower_range": lower_range,
            "upper_range": upper_range,
            "resume_attachment": filename if filename else "",
            "resume_link": resume_link,
            "custom_education": academic_data,
            "custom_external_work_history": work_experience_data
        }

        # Submit to API
        response = requests.post(url, json=form_data, headers=headers)

        if response.status_code == 200:
            # Get the job applicant ID from the response
            response_data = response.json()
            if filename:
                new_name = f"{response_data['data']['name']}.pdf"
                old_path = os.path.join(UPLOAD_FOLDER, filename)
                new_path = os.path.join(UPLOAD_FOLDER, new_name)
                
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)
            flash('FORM SUBMITTED SUCCESSFULLY!', 'success')
        else:
            flash(f'Error: {response.status_code} - {response.text}', 'error')

    except Exception as e:
        flash(f'Error occurred: {str(e)}', 'error')

    return redirect(url_for('home'))

@app.route('/terms')
def tnc():
    return render_template('tnc.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
    #app.run(debug=True)
