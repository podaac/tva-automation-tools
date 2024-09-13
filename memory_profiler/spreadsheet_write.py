import gspread
import csv
import os
from oauth2client.service_account import ServiceAccountCredentials
import sys

# Define the scope for Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Path to your service account credentials JSON file
credentials_path = os.path.expanduser('~/.config/gspread/service_account.json')

# Load credentials
credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)

# Authorize and create a client
client = gspread.authorize(credentials)

# Accept the spreadsheet name as a command-line argument
if len(sys.argv) < 2:
    print("Please provide the Google Sheet name as an argument.")
    sys.exit(1)

spreadsheet_name = sys.argv[1]

# Open the Google Sheets by its name
sheet = client.open(spreadsheet_name)

# Select the first worksheet
worksheet = sheet.get_worksheet(0)

# Read the CSV file
with open('collection_statistics.csv', mode='r') as file:
    reader = csv.reader(file)
    data = list(reader)

# Write CSV data into the Google Sheet
worksheet.update('A1', data)

print(f"CSV data has been written to the Google Sheets: {spreadsheet_name}.")
