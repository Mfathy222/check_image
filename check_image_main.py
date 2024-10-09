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

# دالة للحصول على أقدم صورة بناءً على الاسم
def get_oldest_image_by_name(directory_path):
    # الحصول على جميع الملفات في المجلد
    files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
    
    # تصفية الملفات للحصول على الصور فقط بناءً على الامتدادات الشائعة
    image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    # إذا لم يتم العثور على أي صور في المجلد
    if not image_files:
        return None

    # الحصول على أقدم صورة بناءً على الترتيب الأبجدي للاسم
    oldest_image = min(image_files, key=lambda f: f.lower())
    return oldest_image

# مسار المجلد الذي يحتوي على الصور
directory_path = r'//root/check_image'

# بدء عملية الفحص الدوري للصورة كل 10 دقائق
while True:
    # تشغيل المتصفح
    browser = set_up_driver()
    browser.get("https://bankruptcy.gov.sa/ar/Training/Overview/Pages/QualificationPG.aspx#q-3")
    image_xpath = browser.find_element(By.XPATH, '//*[@id="page-34"]/div/p/img')
    # رابط الصورة من خاصية src
    oldimage_xpath = image_xpath.get_attribute('src')
    # استخراج اسم الصورة من الرابط
    #urlimage_name = os.path.basename(oldimage_xpath)
    urlimage_name = 'AD09102024.jpg'
    # تحميل الصورة باستخدام urllib3 وحفظها بنفس الاسم
    image_url = f'https://bankruptcy.gov.sa/ar/Training/Overview/PublishingImages/{urlimage_name}'
    response = http.request('GET', image_url)
    with open(urlimage_name, 'wb') as file:
        file.write(response.data)

    # الحصول على اسم الصورة القديمة من المجلد بناءً على الاسم
    oldest_image = get_oldest_image_by_name(directory_path)
    print(f"Oldest image in directory: {oldest_image}")
    print(f"Image from website: {urlimage_name}")

    # مقارنة الصورة الجديدة بالصورة القديمة المحفوظة
    if oldest_image == urlimage_name:
        print("The oldest image on your computer matches the image from the website. No new image found.")
    else:
        print(f"The oldest image saved on your computer is not the same as {urlimage_name}")
        # إرسال البريد الإلكتروني عند تغيير الصورة
        email_subject = "Image Change Detected"
        email_body = f"The image on the website has changed. The new image is {urlimage_name}."
        email_sent = send_email(subject=email_subject, body=email_body, attachments=[oldest_image, urlimage_name])

        # حذف الصورة القديمة إذا تم إرسال البريد الإلكتروني بنجاح
        if email_sent and oldest_image:
            old_image_path = os.path.join(directory_path, oldest_image)
            try:
                os.remove(old_image_path)
                print(f"Old image {oldest_image} has been successfully deleted.")
            except Exception as e:
                print(f"Failed to delete old image {oldest_image}: {e}")

    # إغلاق المتصفح بعد الفحص
    browser.quit()

    # الانتظار لمدة 10 دقائق (600 ثانية) قبل إعادة الفحص
    time.sleep(20)  # 600 seconds = 10 minutes

   

   
