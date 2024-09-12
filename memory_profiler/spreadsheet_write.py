import gspread
import csv
from oauth2client.service_account import ServiceAccountCredentials

# Define the scope for Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Path to your service account credentials JSON file
credentials_path = os.path.expanduser('~/.config/gspread/service_account.json')

# Load credentials
credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)

# Authorize and create a client
client = gspread.authorize(credentials)

# Open the Google Sheets by its ID
spreadsheet_id = os.environ['SPREADSHEET_ID']
sheet = client.open_by_key(spreadsheet_id)

# Select the first worksheet
worksheet = sheet.get_worksheet(0)

# Read the CSV file
with open('collection_statistics.csv', mode='r') as file:
    reader = csv.reader(file)
    data = list(reader)

# Write CSV data into the Google Sheet
worksheet.update('A1', data)

print("CSV data has been written to the Google Sheets.")
