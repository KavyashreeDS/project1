from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import json
import random
from datetime import datetime
import os
import gspread
from google.oauth2.service_account import Credentials
from questions import question_bank

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Google Sheets Configuration
SHEET_NAME = 'final'
SPREADSHEET_ID = '1mDbGgtSmsU145tu3qJAWh93HzXT4toaCvVBj7YdSKgo'  # Replace with your Google Sheet ID

def init_google_sheets():
    """Initialize Google Sheets client and ensure header row exists."""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    # Load the JSON string from your Render env var and parse it
    creds_json = os.environ['finalproject']
    creds_dict = json.loads(creds_json)

    # Create credentials from the dict instead of a filename
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1

    # Check if the header row exists, if not, insert it
    if not sheet.row_values(1):
        sheet.insert_row(["Name", "Question", "User Answer", "Correct Answer", "Status", "Timestamp"], 1)
    return sheet

sheet = init_google_sheets()

def get_random_questions(quiz_type, difficulty, count=10):
    """Get random questions from the question bank."""
    questions = question_bank.get(quiz_type, {}).get(difficulty, [])
    if len(questions) < count:
        return questions
    return random.sample(questions, count)

@app.route('/')
def index():
    """Landing page."""
    return render_template('index.html')

@app.route('/submit_user', methods=['POST'])
def submit_user():
    """Handle user form submission."""
    session['user'] = {
        'name': request.form['name'],
        'grade': request.form['grade'],
        'difficulty': request.form['difficulty'],
        'quiz_type': request.form['quiz_type'],
        'timestamp': datetime.now().isoformat()
    }
    return redirect(url_for('summary'))

@app.route('/summary')
def summary():
    """Summary page with formulas and examples."""
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template('summary.html', user=session['user'])

@app.route('/quiz')
def quiz():
    """Quiz page."""
    if 'user' not in session:
        return redirect(url_for('index'))
    
    user = session['user']
    questions = get_random_questions(user['quiz_type'], user['difficulty'])
    session['questions'] = questions
    session['quiz_start_time'] = datetime.now().isoformat()
    
    return render_template('quiz.html', questions=questions, user=user)

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    """Handle quiz submission."""
    if 'user' not in session or 'questions' not in session:
        return redirect(url_for('index'))
    
    user = session['user']
    questions = session['questions']
    answers = request.json.get('answers', [])
    
    # Calculate score
    correct_answers = 0
    for i, question in enumerate(questions):
        if i < len(answers) and answers[i] == question['correct']:
            correct_answers += 1
    
    # Calculate time taken
    start_time = datetime.fromisoformat(session['quiz_start_time'])
    end_time = datetime.now()
    time_taken = int((end_time - start_time).total_seconds())
    
    percentage = round((correct_answers / len(questions)) * 100)
    
    # Prepare result data
    result = {
        'name': user['name'],
        'grade': user['grade'],
        'difficulty': user['difficulty'],
        'quiz_type': user['quiz_type'],
        'score': correct_answers,
        'total_questions': len(questions),
        'percentage': percentage,
        'time_taken': time_taken,
        'timestamp': datetime.now().isoformat()
    }
    
    # Save to Google Sheets
    save_to_google_sheets(result)
    
    # Save to local file as backup
    try:
        with open('quiz_results.json', 'r') as f:
            results = json.load(f)
    except FileNotFoundError:
        results = []
    
    results.append(result)
    
    with open('quiz_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    session['last_result'] = result
    return jsonify({'success': True, 'result': result})

def save_to_google_sheets(data):
    """Save quiz result to Google Sheets."""
    try:
        sheet = init_google_sheets()
        row = [
            data['name'],
            data['grade'],
            data['difficulty'],
            data['quiz_type'],
            data['score'],
            data['total_questions'],
            data['percentage'],
            data['time_taken'],
            data['timestamp']
        ]
        sheet.append_row(row)
    except Exception as e:
        print(f"Error saving to Google Sheets: {e}")

@app.route('/results')
def results():
    """Results page with leaderboard."""
    try:
        with open('quiz_results.json', 'r') as f:
            all_results = json.load(f)
    except FileNotFoundError:
        all_results = []
    
    # Sort by percentage (desc) then by time (asc)
    leaderboard = sorted(all_results, key=lambda x: (-x['percentage'], x['time_taken']))[:10]
    
    last_result = session.get('last_result')
    
    return render_template('results.html', 
                         leaderboard=leaderboard, 
                         last_result=last_result)

@app.route('/progress')
def progress():
    """Progress page showing user's quiz history."""
    if 'user' not in session:
        return redirect(url_for('index'))
    
    user = session['user']
    
    try:
        with open('quiz_results.json', 'r') as f:
            all_results = json.load(f)
    except FileNotFoundError:
        all_results = []
    
    # Filter results for current user
    user_results = [r for r in all_results if r['name'] == user['name']]
    user_results.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Calculate stats
    stats = {
        'total_quizzes': len(user_results),
        'avg_score': round(sum(r['percentage'] for r in user_results) / len(user_results)) if user_results else 0,
        'best_score': max(r['percentage'] for r in user_results) if user_results else 0,
        'total_time': sum(r['time_taken'] for r in user_results) if user_results else 0
    }
    
    return render_template('progress.html', 
                         user=user, 
                         user_results=user_results[:10], 
                         stats=stats)


@app.route('/reset')
def reset():
    """Reset session and go back to landing page"""
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
