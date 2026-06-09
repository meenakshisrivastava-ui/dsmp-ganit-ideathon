import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(from_addr, to_addr, subject, body):
    msg = MIMEMultipart()
    msg['From']    = from_addr
    msg['To']      = to_addr
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    smtp = smtplib.SMTP('localhost', 1025)   # MailHog SMTP port
    smtp.send_message(msg)
    smtp.quit()
    print(f" Sent → {to_addr}")

# --- Send a simple test email ---
send_email(
    from_addr = "system@dsmp-corp.io",
    to_addr   = "meenakshi.srivastava@dsmp-corp.io",
    subject   = "Test Email",
    body      = "Hello Meenakshi, this is a test message."
)