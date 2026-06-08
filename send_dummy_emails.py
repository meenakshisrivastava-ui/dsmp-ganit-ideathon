import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── Your dummy team ──────────────────────────────────────────────
TEAM = [
    {"name": "Rahul Sharma",   "email": "rahul.sharma@dsmp-corp.io"},
    {"name": "Priya Verma",    "email": "priya.verma@dsmp-corp.io"},
    {"name": "DevOps Lead",    "email": "devops.lead@dsmp-corp.io"},
    {"name": "HR Manager",     "email": "hr.manager@dsmp-corp.io"},
    {"name": "Finance Head",   "email": "finance.head@dsmp-corp.io"},
]

# ── Sensitive email templates ─────────────────────────────────────
EMAILS = [
    {
        "subject": "Payroll Details - Confidential",
        "body": """Hi {name},

Please find your payroll details below:

Employee ID   : ENG-1042
Full Name     : {name}
Aadhaar No.   : 3456 7890 1234
PAN           : ABCDE1234F
Salary        : Rs.24,00,000/yr
Bank Account  : 9876543210
IFSC Code     : HDFC0001234

Do not share this email with anyone.

Regards,
HR Team"""
    },
    {
        "subject": "AWS Credentials - Internal Use Only",
        "body": """Hi {name},

Your AWS access credentials have been reset:

AWS Access Key ID     : AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key : wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Region                : ap-south-1
Console URL           : https://console.aws.amazon.com

Please rotate these within 24 hours.

Regards,
DevOps Team"""
    },
    {
        "subject": "Database Password Reset",
        "body": """Hi {name},

Your database credentials have been updated:

Host        : db.dsmp-corp.internal
Port        : 5432
Username    : {name}
Password    : Tr0ub4dor&3!xK9
Database    : production_db

Please update your local config file.

Regards,
IT Support"""
    },
    {
        "subject": "Employee Personal Details - HR Records",
        "body": """Hi {name},

Please verify your personal details on file:

Full Name     : {name}
Date of Birth : 15/08/1990
Phone         : +91 98765 43210
Personal Mail : {name}@gmail.com
Address       : 42, MG Road, Bengaluru - 560001
Emergency No. : +91 91234 56789

Reply if any corrections needed.

Regards,
HR Team"""
    },
    {
        "subject": "Credit Card Expense Report",
        "body": """Hi {name},

Your corporate card details for Q1 expense report:

Card Number  : 4111 1111 1111 1111
Expiry       : 12/26
CVV          : 123
Card Holder  : {name}
Total Spent  : Rs.87,450

Please submit receipts by Friday.

Regards,
Finance Team"""
    },
]

# ── Send all emails ───────────────────────────────────────────────
def send_email(from_addr, to_addr, subject, body):
    msg = MIMEMultipart()
    msg['From']    = from_addr
    msg['To']      = to_addr
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    smtp = smtplib.SMTP('localhost', 1025)
    smtp.send_message(msg)
    smtp.quit()

print("📨 Sending dummy emails...\n")

for member in TEAM:
    for template in EMAILS:
        subject = template['subject']
        body    = template['body'].format(name=member['name'])
        sender  = random.choice(TEAM)['email']

        send_email(
            from_addr = sender,
            to_addr   = member['email'],
            subject   = subject,
            body      = body
        )
        print(f"    To: {member['email']:<35} | Subject: {subject}")

print(f"\n Done! {len(TEAM) * len(EMAILS)} emails sent.")
print(" Open http://localhost:8025 to see them all")