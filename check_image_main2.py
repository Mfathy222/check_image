import time
import os
# Set environment variable to suppress webdriver_manager logs
os.environ['WDM_LOG_LEVEL'] = '0'  # Must be set before importing webdriver_manager

import urllib3
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Suppress webdriver_manager logs
logging.getLogger('WDM').setLevel(logging.ERROR)
# Alternatively, if the logger name is 'webdriver_manager':
# logging.getLogger('webdriver_manager').setLevel(logging.ERROR)

# Email configuration
SENDER_EMAIL = "app@sijiltech.com"
SENDER_PASSWORD = "@Zofirm619"
RECEIVER_EMAIL = "mohammed.fathy@sijiltech.com"
CC_EMAIL = "abosetta@zofirm.com"
SMTP_SERVER = "mail.sijiltech.com"  # For example, "smtp.gmail.com"
SMTP_PORT = 465  # SMTP over SSL

# Disable InsecureRequestWarning warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set up connection manager using urllib3
http = urllib3.PoolManager(cert_reqs='CERT_NONE')

def set_up_driver():
    """Set up Chrome WebDriver in headless mode."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run browser in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    # Set up browser service using ChromeDriverManager
    service = Service(ChromeDriverManager().install())
    # Create a Chrome browser using the service and settings
    browser = webdriver.Chrome(service=service, options=chrome_options)
    return browser

def send_email(subject, body, attachments=None):
    """Send an email with optional attachments."""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['CC'] = CC_EMAIL
        msg['Subject'] = subject

        # Attach message text
        msg.attach(MIMEText(body, 'plain'))

        # Add attachments (images) if they exist
        if attachments:
            for attachment in attachments:
                if os.path.isfile(attachment):
                    with open(attachment, 'rb') as file:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(file.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment)}')
                        msg.attach(part)
                else:
                    logging.warning(f"Attachment {attachment} does not exist.")

        # Email SMTP Settings
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        logging.info("Email sent successfully.")
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        return False

def print_current_time(label):
    """Print the current time with a specific label."""
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logging.info(f"{label}: {current_time}")

def get_oldest_image_by_name(directory_path):
    """Get the oldest image in the directory based on alphabetical order."""
    try:
        # Get all files in the folder
        files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
        # Filter files to get only images based on common extensions
        image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not image_files:
            return None
        # Get the oldest image based on alphabetical order
        oldest_image = min(image_files, key=lambda f: f.lower())
        return oldest_image
    except Exception as e:
        logging.error(f"Error getting the oldest image: {e}")
        return None

def main():
    # Path of the folder containing the images (specified directory path)
    directory_path = r'//root/check_image'

    # Ensure the directory exists
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    # Change working directory to the specified path
    os.chdir(directory_path)

    # Wait time between scans (in seconds)
    wait_time = 3600  # 60 minutes

    while True:
        print_current_time("Start checking at")

        try:
            # Set up browser
            browser = set_up_driver()
            browser.get("https://bankruptcy.gov.sa/ar/Training/Overview/Pages/QualificationPG.aspx#q-3")

            # Wait for the image element to be present
            wait = WebDriverWait(browser, 15)
            image_element = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="page-34"]/div/p/img')))
            # Get the image source URL
            image_src = image_element.get_attribute('src')
            image_name = os.path.basename(image_src)
            #image_name='AD09102024.jpg'

            # Download the image using urllib3 and save it with the same name
            image_url = f'https://bankruptcy.gov.sa/ar/Training/Overview/PublishingImages/{image_name}'
            response = http.request('GET', image_url)
            with open(image_name, 'wb') as file:
                file.write(response.data)
            logging.info(f"Downloaded image: {image_name}")

            # Get the oldest image from the directory
            oldest_image = get_oldest_image_by_name(directory_path)
            logging.info(f"Oldest image in directory: {oldest_image}")
            logging.info(f"Image from website: {image_name}")

            # Compare the new image with the old saved image
            if oldest_image == image_name:
                logging.info("No new image found. The image has not changed.")
            else:
                logging.info(f"New image detected: {image_name}")
                # Send email when the image has changed
                email_subject = "Image Change Detected"
                email_body = f"The image on the website has changed. The new image is {image_name}."
                attachments = []
                if oldest_image:
                    attachments.append(oldest_image)
                attachments.append(image_name)
                email_sent = send_email(subject=email_subject, body=email_body, attachments=attachments)

                # Delete old image if the email was sent successfully
                if email_sent and oldest_image:
                    old_image_path = os.path.join(directory_path, oldest_image)
                    try:
                        os.remove(old_image_path)
                        logging.info(f"Old image {oldest_image} has been successfully deleted.")
                    except Exception as e:
                        logging.error(f"Failed to delete old image {oldest_image}: {e}")
        except Exception as e:
            logging.error(f"An error occurred: {e}")
        finally:
            # Close browser after scanning
            browser.quit()

        print_current_time("Last check at")

        # Countdown before the next scan
        total_wait_time = wait_time  # total wait time in seconds
        logging.info(f"Waiting for {wait_time // 60} minutes before the next check.")

        while total_wait_time > 0:
            mins, secs = divmod(total_wait_time, 60)
            print(f"Next scan will start in {mins} minutes and {secs} seconds...", end='\r')
            time.sleep(1)
            total_wait_time -= 1
        print("\n")  # Move to the next line after countdown completes

if __name__ == "__main__":
    main()
