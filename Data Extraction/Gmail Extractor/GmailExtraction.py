# import the required libraries
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os.path
import base64
import email
from bs4 import BeautifulSoup
import re
import traceback
from pymongo import MongoClient

# Define the SCOPES. If modifying it, delete the token.pickle file.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

service=None

def getAutheticationAndConnection():
 # Variable creds will store the user access token.
 # If no valid token found, we will create one.
 creds = None

 # The file token.pickle contains the user access token.
 # Check if it exists
 if os.path.exists('token.pickle'):

  # Read the token from the file and store it in the variable creds
  with open('token.pickle', 'rb') as token:
   creds = pickle.load(token)

 # If credentials are not available or are invalid, ask the user to log in.
 if not creds or not creds.valid:
  if creds and creds.expired and creds.refresh_token:
   creds.refresh(Request())
  else:
   flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
   creds = flow.run_local_server(port=0)

  # Save the access token in token.pickle file for the next run
  with open('token.pickle', 'wb') as token:
   pickle.dump(creds, token)

 # Connect to the Gmail API
 global service
 service = build('gmail', 'v1', credentials=creds)



def clean_email_content(subject, sender, body, received_date, redirect_link):
    """
    Cleans and formats email content for database storage with error handling.
    """
    print(body)
    try:
        # Clean subject
        clean_subject = subject.strip() if subject else None
        if not clean_subject:
            raise ValueError("Subject is missing or empty.")

        # Clean sender
        clean_sender = sender.strip() if sender else None
        if not clean_sender:
            raise ValueError("Sender is missing or empty.")

        # Clean body
        body = re.sub(r'<[^>]+>', '', body)
         # Remove extra whitespace and newlines
        body = re.sub(r'\s+', ' ', body)
        clean_body = re.sub(r"\s{2,}", " ", body).strip() if body else None
        
        
        # Remove leading/trailing whitespace
        body = body.strip()
        if not clean_body:
            raise ValueError("Body is missing or empty.")

        # Clean received date
        clean_received_date = received_date.strip() if received_date else None
        if not clean_received_date:
            raise ValueError("Received date is missing or empty.")

        # Clean redirect link
        clean_redirect_link = redirect_link.strip() if redirect_link else None
        if not clean_redirect_link:
            raise ValueError("Redirect link is missing or empty.")

        # Construct a dictionary for structured data
        email_data = {
            "subject": clean_subject,
            "sender": clean_sender,
            "body": clean_body,
            "received_date": clean_received_date,
            "redirect_link": clean_redirect_link,
        }

        return email_data

    except Exception as e:
        # Log the error and the failing input
        traceback.print_exc()
        print(f"Error while cleaning email content: {e.printstack}")
        #print(f"Inputs:\n Subject: {subject}\n Sender: {sender}\n Body: {body}\n Received Date: {received_date}\n Redirect Link: {redirect_link}")
        return None
    
# Function to connect to MongoDB and insert data
def store_to_mongodb(data, db_name="email_data", collection_name="emails"):
    """
    Stores cleaned email data to MongoDB.
    """
    try:
        # Connect to MongoDB (local)
        client = MongoClient("mongodb://localhost:27017/")
        db = client[db_name]
        collection = db[collection_name]

        # Insert the data
        result = collection.insert_many(data)
        print(f"Data inserted with ID: {result.inserted_ids}")

    except Exception as e:
        print(f"Error while connecting to MongoDB: {e}")
        traceback.print_exc()

def getParsedContent(numberOfEmails):
    global service
    redirect_links = []
    result_emails=[]
    result = service.users().messages().list(userId='me',maxResults=min(50,numberOfEmails)).execute()
    messages = result.get('messages')
    numberOfEmails-=50
    while 'nextPageToken' in result and numberOfEmails>0:
        page_token = result['nextPageToken']
        result = service.users().messages().list(userId="me", maxResults=50, pageToken=page_token).execute()
        if 'messages' in result:
            messages.extend(result['messages'])
            numberOfEmails-=50
    for msg in messages:
    # Get the message from its id
        txt = service.users().messages().get(userId='me', id=msg['id']).execute()
        redirect_link = f"https://mail.google.com/mail/u/0/#all/{msg['id']}"
        #print("in message loop" + str(txt))
        try:
            payload = txt['payload']
            headers = payload['headers']

            # Look for Subject and Sender Email in the headers
            for d in headers:
                if d['name'] == 'Subject':
                    subject = d['value']
                if d['name'] == 'From':
                    sender = d['value']
                if d['name'] == 'Date':
                    received_date= d['value']
            # The Body of the message is in Encrypted format. So, we have to decode it.
            # Get the data and decode it with base 64 decoder.
            if payload.get('parts'):
                parts = payload.get('parts')[0]
                data = parts['body']['data']
            elif payload.get('body', {}).get('data'):
                data = payload['body']['data']
            else:
                print("No readable content found in this message.")

            data = data.replace("-","+").replace("_","/")
            decoded_data = base64.b64decode(data)

            # Now, the data obtained is in lxml. So, we will parse
            # it with BeautifulSoup library
            soup = BeautifulSoup(decoded_data , "lxml")
            body = soup.body()
            # Printing the subject, sender's email and message
            cleaned_email = clean_email_content(subject, sender,str(body), received_date, redirect_link)
            print("Subject: ",cleaned_email['subject'])
            print("From: ", cleaned_email['sender'])
            print("Message: ",cleaned_email['body'])
            print("Recieved Date",cleaned_email['received_date'])
            print("Redirect link ",cleaned_email['redirect_link'])
            print('\n')
            result_emails.append(cleaned_email)
        except Exception  as e:
            traceback.print_exc()

            pass
    return result_emails

getAutheticationAndConnection()
result_for_db=getParsedContent(100)
store_to_mongodb(result_for_db)