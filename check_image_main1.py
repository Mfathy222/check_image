import time
import os
import urllib3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Email configuration
SENDER_EMAIL = "app@sijiltech.com"
SENDER_PASSWORD = "@Zofirm619"
RECEIVER_EMAIL = "mohammed.fathy@sijiltech.com"
CC_EMAIL = "abosetta@zofirm.com"
SMTP_SERVER = "mail.sijiltech.com"
SMTP_PORT = 465  # SMTP over SSL

# Disable InsecureRequestWarning warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set up connection manager using urllib3
http = urllib3.PoolManager(cert_reqs='CERT_NONE')

def set_up_driver():
    # Setting browser options
    chrome_options = Options()
    # Run the browser in invisible mode
    chrome_options.add_argument("--headless")
    # Disable GPU acceleration
    chrome_options.add_argument("--disable-gpu")
    # Bypass the security model
    chrome_options.add_argument("--no-sandbox")
    # Setting window size
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_experimental_option("detach", True)
    # Set up browser service using ChromeDriverManager
    service = Service(ChromeDriverManager().install())
    # Create a Chrome browser using the service and settings
    browser = webdriver.Chrome(service=service, options=chrome_options)
    return browser

def send_email(subject, body, attachments=None):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['CC'] = CC_EMAIL
    msg['Subject'] = subject

    # Attach message text
    msg.attach(MIMEText(body, 'plain'))

    # Add the attachments (images) if they exist
    if attachments:
        for attachment in attachments:
            with open(attachment, 'rb') as file:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(file.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment)}')
                msg.attach(part)

    # Email SMTP Settings
    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully.")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
# Present time function
def print_current_time(label):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"{label}: {current_time}")

# Function to get oldest image based on name
def get_oldest_image_by_name(directory_path):
    # Get all files in the folder
    files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
    
    # Filter files to get only images based on common extensions.
    image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    # If no images are found in the folder
    if not image_files:
        return None

    # Get oldest image based on name alphabetical order
    oldest_image = min(image_files, key=lambda f: f.lower())
    return oldest_image

# Path of the folder containing the images
directory_path = r'//root/check_image'

# Start the image scanning process every 60 minutes
while True:
    print_current_time("Start checking at")

    # Run browser
    browser = set_up_driver()
    browser.get("https://bankruptcy.gov.sa/ar/Training/Overview/Pages/QualificationPG.aspx#q-3")
    image_xpath = browser.find_element(By.XPATH, '//*[@id="page-34"]/div/p/img')
    # Image link from src property
    oldimage_xpath = image_xpath.get_attribute('src')
    urlimage_name = os.path.basename(oldimage_xpath)
    urlimage_name='AD09102024.jpg'
    
    # Upload the image using urllib3 and save it with the same name
    image_url = f'https://bankruptcy.gov.sa/ar/Training/Overview/PublishingImages/{urlimage_name}'
    response = http.request('GET', image_url)
    with open(urlimage_name, 'wb') as file:
        file.write(response.data)

    # Get old image name from folder based on name
    oldest_image = get_oldest_image_by_name(directory_path)
    print(f"Oldest image in directory: {oldest_image}")
    print(f"Image from website: {urlimage_name}")

    # Compare the new image with the old saved image.
    if oldest_image == urlimage_name:
        print("No new image found. The image has not changed.")
    else:
        print(f"The oldest image saved on your computer is not the same as {urlimage_name}")
        
        # Send email when image is changed
        email_subject = "Image Change Detected"
        email_body = f"The image on the website has changed. The new image is {urlimage_name}."
        email_sent = send_email(subject=email_subject, body=email_body, attachments=[oldest_image, urlimage_name])

        # Delete old image if email is sent successfully
        if email_sent and oldest_image:
            old_image_path = os.path.join(directory_path, oldest_image)
            try:
                os.remove(old_image_path)
                print(f"Old image {oldest_image} has been successfully deleted.")
            except Exception as e:
                print(f"Failed to delete old image {oldest_image}: {e}")
    # Close browser after scanning
    browser.quit()
    print_current_time("Last check at")

    # Wait 60 minutes before re-scanning.
    countdown_time = 3600  
    while countdown_time > 0:
        mins, secs = divmod(countdown_time, 60)
        print(f"Next check will start in: {mins} minutes, {secs} seconds", end="\r")
        time.sleep(1)
        countdown_time -= 1
    print("\nStarting new check cycle...\n")


