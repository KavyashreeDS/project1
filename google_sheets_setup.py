"""
Google Sheets Setup Instructions

To integrate with Google Sheets, follow these steps:

1. Go to Google Cloud Console (https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Sheets API
4. Create credentials (Service Account)
5. Download the JSON key file
6. Share your Google Sheet with the service account email
7. Update the SPREADSHEET_ID in app.py

Example Google Sheets setup:
"""

import gspread
from google.oauth2.service_account import Credentials

def setup_google_sheets():
    # Define the scope
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    # Path to your service account key file
    SERVICE_ACCOUNT_FILE = 'C:\Users\STUDENT\Desktop\project\finalproject-467609-4bb734160999.json'
    
    # Authenticate and create the service
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    
    client = gspread.authorize(credentials)
    
    # Your Google Sheet ID (from the URL)
    SPREADSHEET_ID = 'your-google-sheet-id-here'
    
    # Open the spreadsheet
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    
    # Set up headers if needed
    headers = [
        'Name', 'Grade', 'Difficulty', 'Quiz Type', 
        'Score', 'Total Questions', 'Percentage', 
        'Time Taken (seconds)', 'Timestamp'
    ]
    
    # Check if headers exist, if not add them
    if not sheet.get_all_values():
        sheet.append_row(headers)
    
    return sheet

def save_quiz_result(sheet, result_data):
    """Save a quiz result to Google Sheets"""
    row = [
        result_data['name'],
        result_data['grade'],
        result_data['difficulty'],
        result_data['quiz_type'],
        result_data['score'],
        result_data['total_questions'],
        result_data['percentage'],
        result_data['time_taken'],
        result_data['timestamp']
    ]
    sheet.append_row(row)

# Example usage:
if __name__ == "__main__":
    try:
        sheet = setup_google_sheets()
        print("Google Sheets setup successful!")
        
        # Test data
        test_result = {
            'name': 'Test Student',
            'grade': '10',
            'difficulty': 'medium',
            'quiz_type': 'simple',
            'score': 8,
            'total_questions': 10,
            'percentage': 80,
            'time_taken': 300,
            'timestamp': '2024-01-01T12:00:00'
        }
        
        save_quiz_result(sheet, test_result)
        print("Test result saved successfully!")
        
    except Exception as e:
        print(f"Error setting up Google Sheets: {e}")