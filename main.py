import hashlib
import requests
from google.cloud import storage
from google.cloud import secretmanager
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import logging


def send_email(subject, message, from_addr, to_addr, smtp_server, smtp_port, password):
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    body = message
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(from_addr, password)
    text = msg.as_string()
    server.sendmail(from_addr, to_addr, text)
    server.quit()

def check_website(request):
    project_id = 'website-checker-v2'
    secret_manager = secretmanager.SecretManagerServiceClient()
    sender_email = secret_manager.access_secret_version(name=f"projects/{project_id}/secrets/sender_email/versions/latest").payload.data.decode('UTF-8')
    receiver_email = secret_manager.access_secret_version(name=f"projects/{project_id}/secrets/receiver_email/versions/latest").payload.data.decode('UTF-8')
    sender_password = secret_manager.access_secret_version(name=f"projects/{project_id}/secrets/sender_password/versions/latest").payload.data.decode('UTF-8')
    
    url = "https://www.ticketone.it/artist/cigarettes-after-sex/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    status_code = response.status_code
    current_hash = hashlib.sha224(response.text.encode('utf-8')).hexdigest()
    
    client = storage.Client()
    bucket = client.get_bucket('website_hashing_response')
    blob = storage.Blob('website_data.txt', bucket)
    
    if blob.exists(client):
        old_hash = blob.download_as_text()
    else:
        old_hash = ''

    blob.upload_from_string(current_hash)

    if old_hash != current_hash:
        send_email(
            'Website Content Changed!',
            f'Ciao. The content of the website {url} has changed. Status code here: {status_code}',
            sender_email,
            receiver_email,
            'smtp.gmail.com',
            587,
            sender_password
        )
        return 'Website content changed', 200
    else:
        send_email(
            'Website Content Unchanged..',
            f'Ciao. The content of the website {url} has not changed. Status code here: {status_code}',
            sender_email,
            receiver_email,
            'smtp.gmail.com',
            587,
            sender_password
        )
        return 'Website content unchanged', 200

if __name__ == '__main__':
    logging.info("ciao")
    check_website(request=None)
