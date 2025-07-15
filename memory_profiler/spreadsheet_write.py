import gspread
import csv
import os
from oauth2client.service_account import ServiceAccountCredentials
import sys

# Authorize and create a client
client = gspread.service_account()

# Open the Google Sheets by its ID
spreadsheet_id = os.environ['SPREADSHEET_ID']
sheet = client.open_by_key(spreadsheet_id)

# Accept the worksheet name as a command-line argument
if len(sys.argv) < 2:
    print("Please provide the worksheet name as a command-line argument.")
    sys.exit(1)

# Select the worksheet name from the command-line argument
worksheet_name = sys.argv[1]
worksheet = sheet.worksheet(worksheet_name)

# Read the CSV file
with open('collection_statistics.csv', mode='r') as file:
    reader = csv.reader(file)
    data = list(reader)

# Write CSV data into the Google Sheet
worksheet.update(data, 'A1')

print(f"CSV data has been written to the Google Sheets in worksheet '{worksheet_name}'.")
