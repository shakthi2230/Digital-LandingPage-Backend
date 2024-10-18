from fastapi import FastAPI, HTTPException, Form
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
from fastapi.middleware.cors import CORSMiddleware
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import logging

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'shakthi',
    'database': 'digital',
}

app = FastAPI()

origins = [
    "http://localhost:3000",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

class Contact(BaseModel):
    name: str
    email: str
    phone: str
    country: str
    state: str
    city: str
    message: str

# Email configuration
SENDER_EMAIL = "harsh.shakthi@gmail.com"
PASSWORD = "phxe ujmb evtl tdal"  # Replace with your actual email password

# Email sending function
async def send_email(contact: Contact):
    receiver_email = "sakthivelmaadhu26@gmail.com"  # Send email to the contact's email address

    # Prepare the email content
    current_date = datetime.date.today().strftime("%d-%m-%Y")
    subject = f"Contact Form Submission from {contact.name}"
    body = f"""
    <html>
<body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; color: #333;">
    <div style="max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);">
        <h2 style="color: #007bff; text-align: center; border-bottom: 2px solid #007bff; padding-bottom: 10px;">Contact Form Submission</h2>
        <div style="margin-top: 20px; padding: 10px; border: 1px solid #eaeaea; border-radius: 4px; background-color: #f9f9f9;">
            <p style="margin: 15px 0; font-size: 16px;"><strong>Name:</strong> {contact.name}</p>
            <p style="margin: 15px 0; font-size: 16px;"><strong>Email:</strong> {contact.email}</p>
            <p style="margin: 15px 0; font-size: 16px;"><strong>Phone:</strong> {contact.phone}</p>
            <p style="margin: 15px 0; font-size: 16px;"><strong>Country:</strong> {contact.country}</p>
            <p style="margin: 15px 0; font-size: 16px;"><strong>State:</strong> {contact.state}</p>
            <p style="margin: 15px 0; font-size: 16px;"><strong>City:</strong> {contact.city}</p>
            <p style="margin: 15px 0; font-size: 16px;"><strong>Message:</strong> {contact.message}</p>
            <p style="margin: 15px 0; font-size: 16px;"><strong>Date:</strong> {current_date}</p>
        </div>
        <div style="text-align: center; margin-top: 20px; font-size: 14px; color: #666;">
            Thank you for reaching out! We will get back to you soon.
        </div>
    </div>
</body>
</html>

    """

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        # Connect to SMTP server and send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        server.quit()
        
        logging.info("Email sent successfully to %s", receiver_email)
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("Connected to MySQL database")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

def create_table():
    connection = create_connection()
    cursor = connection.cursor()
    create_table_query = """
    CREATE TABLE IF NOT EXISTS contacts (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL,
        phone VARCHAR(15) NOT NULL,
        country VARCHAR(50) NOT NULL,
        state VARCHAR(50),
        city VARCHAR(50),
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    cursor.execute(create_table_query)
    connection.commit()
    cursor.close()
    connection.close()

create_table()

@app.post("/contact/")
async def create_contact(contact: Contact):
    connection = create_connection()
    cursor = connection.cursor()
    
    insert_query = """
    INSERT INTO contacts (name, email, phone, country, state, city, message) 
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    contact_data = (
        contact.name,
        contact.email,
        contact.phone,
        contact.country,
        contact.state,
        contact.city,
        contact.message
    )

    try:
        cursor.execute(insert_query, contact_data)
        connection.commit()
        
        # Send email after saving the contact
        await send_email(contact)
        
        return {"message": "Contact saved successfully", "id": cursor.lastrowid}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
