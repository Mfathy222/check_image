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


class ImageChecker:
    def __init__(self, directory_path):
        self.directory_path = directory_path
        # Ensure the directory exists
        if not os.path.exists(self.directory_path):
            os.makedirs(self.directory_path)
        # Change working directory to the specified path
        os.chdir(self.directory_path)
        self.http = urllib3.PoolManager(cert_reqs='CERT_NONE')
        self.browser = None

    def set_up_driver(self):
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
        self.browser = webdriver.Chrome(service=service, options=chrome_options)

    def send_email(self, subject, body, attachments=None):
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
                if os.path.isfile(attachment):
                    with open(attachment, 'rb') as file:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(file.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition',
                                        f'attachment; filename={os.path.basename(attachment)}')
                        msg.attach(part)
                else:
                    print(f"Attachment {attachment} not found.")

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

    def print_current_time(self, label):
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(f"{label}: {current_time}")

    def get_image_files(self, extension_list=('.png', '.jpg', '.jpeg')):
        return [f for f in os.listdir(self.directory_path)
                if os.path.isfile(os.path.join(self.directory_path, f)) and f.lower().endswith(extension_list)]

    def get_oldest_image_by_name(self):
        image_files = self.get_image_files()
        if not image_files:
            return None
        oldest_image = min(image_files, key=lambda f: f.lower())
        return oldest_image

    def get_newest_image_by_name(self):
        image_files = self.get_image_files()
        if not image_files:
            return None
        newest_image = max(image_files, key=lambda f: f.lower())
        return newest_image

    def check_image(self):
        self.print_current_time("Start checking at")

        try:
            # Run browser
            self.set_up_driver()
            self.browser.get("https://bankruptcy.gov.sa/ar/Training/Overview/Pages/QualificationPG.aspx#q-3")
            image_xpath = self.browser.find_element(By.XPATH, '//*[@id="page-34"]/div/p/img')
            # Image link from src property
            oldimage_xpath = image_xpath.get_attribute('src')
            urlimage_name = os.path.basename(oldimage_xpath)
            # urlimage_name = 'AD09102024.jpg'

            # Download the image using urllib3 and save it with the same name on website
            image_url = f'https://bankruptcy.gov.sa/ar/Training/Overview/PublishingImages/{urlimage_name}'
            response = self.http.request('GET', image_url)
            with open(urlimage_name, 'wb') as file:
                file.write(response.data)

            # Get old image name from folder based on name
            oldest_image = self.get_oldest_image_by_name()
            print(f"Oldest image in directory: {oldest_image}")
            print(f"Image from website: {urlimage_name}")

            # Get newest image name from folder based on name
            newest_image = self.get_newest_image_by_name()
            print(f"Newest image downloaded in directory: {newest_image}")

            # Compare the new image with the old saved image.
            if oldest_image == newest_image:
                print("No new image found. The image has not changed.")
            else:
                print(f"The oldest image saved on your computer is not the same as {urlimage_name}")

                # Send email when image is changed
                email_subject = "Image Change Detected And New Training Found On Website"
                email_body = f"The image on the website has changed. And New Training in this image {newest_image}."
                email_sent = self.send_email(subject=email_subject, body=email_body,
                                             attachments=[oldest_image, newest_image])

                # Delete old image if email is sent successfully
                if email_sent and oldest_image:
                    old_image_path = os.path.join(self.directory_path, oldest_image)
                    try:
                        os.remove(old_image_path)
                        print(f"Old image {oldest_image} has been successfully deleted.")
                    except Exception as e:
                        print(f"Failed to delete old image {oldest_image}: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # Close browser after scanning
            if self.browser:
                self.browser.quit()
            self.print_current_time("Last check at")

    def start(self, interval=3600):
        while True:
            self.check_image()

            # Wait before re-scanning.
            countdown_time = interval
            while countdown_time > 0:
                mins, secs = divmod(countdown_time, 60)
                print(f"Next check will start in: {mins} minutes, {secs} seconds", end="\r")
                time.sleep(1)
                countdown_time -= 1
            print("\nStarting new check cycle...\n")


if __name__ == "__main__":
    # Path of the folder containing the images
    directory_path = r'//root/check_image'

    # Create an instance of ImageChecker
    image_checker = ImageChecker(directory_path)

    # Start the image scanning process every 60 minutes
    image_checker.start(interval=3600)



    #image_url      = Static url for image to download 
    #urlimage_name  = dynamic Image Name taken from xpath on website  
    #oldest_image   = Old Image Name from directory_path
    #newest_image   = New Image Name from directory_path
    #directory_path = Saved Image on Driver
