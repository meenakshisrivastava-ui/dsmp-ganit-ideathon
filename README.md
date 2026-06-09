# Autonomous Unstructured Data Risk Mapper (DSMP Module)

> A self-hosted, open-source pipeline that continuously extracts metadata from unstructured data sources — emails, chat messages, and documents — detects sensitive information (PII, credentials, financial data), scores risk, and pushes structured findings to AWS S3 for compliance monitoring and auditing.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Setup Guide](#setup-guide)
  - [1. Local Development Setup](#1-local-development-setup)
  - [2. AWS Setup](#2-aws-setup)
  - [3. Server Deployment (AWS EC2)](#3-server-deployment-aws-ec2)
- [Running the Pipeline](#running-the-pipeline)
- [Scheduling](#scheduling)
- [Monitoring](#monitoring)
- [Security](#security)
- [Troubleshooting](#troubleshooting)

---

## Overview

Enterprises struggle to continuously identify and monitor sensitive data spread across emails, documents, and chat systems. Manual classification and basic pattern-matching tools fail to capture exposure or context, creating compliance blind spots.

This module solves that by:

- Connecting to **MailHog** (dummy SMTP) and **Mattermost** (self-hosted chat) as data sources
- Extracting and normalising metadata from all messages and posts
- Pushing structured JSON metadata to **AWS S3** for downstream NLP processing
- Running automatically on a scheduled cron job every 15 minutes
- Producing findings ready for PII detection, risk scoring, and compliance reporting

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  AWS EC2 (Ubuntu 22.04)                      │
│                                                              │
│   Docker Containers                                          │
│   ├── MailHog          (port 1025 SMTP / 8025 UI)           │
│   ├── Mattermost       (port 8065)                          │
│   └── PostgreSQL       (Mattermost DB, internal)            │
│                                                              │
│   Python Pipeline (cron every 15 min)                        │
│   ├── extract_mailhog.py    → pulls email metadata          │
│   ├── extract_mattermost.py → pulls chat metadata           │
│   ├── push_to_s3.py         → uploads JSON to AWS S3        │
│   └── run_pipeline.py       → orchestrates full run         │
└─────────────────────────────────────────────────────────────┘
              │                          │
              ▼                          ▼
       EC2 Public IP               AWS S3 Buckets
  MailHog  → :8025            dsmp-email-metadata/
  Mattermost → :8065          dsmp-chat-metadata/
```

---

## Tech Stack

| Component | Tool | Purpose |
|---|---|---|
| Dummy email server | MailHog | Catch-all SMTP + REST API |
| Dummy chat platform | Mattermost CE | Self-hosted team messaging |
| Database | PostgreSQL 15 | Mattermost backend DB |
| Object storage | AWS S3 | Metadata and findings storage |
| Pipeline language | Python 3.14 | Extraction and upload scripts |
| Containerisation | Docker + Compose | Run all services locally/on server |
| Scheduling | Linux Cron | Auto-run pipeline every 15 min |
| Server | AWS EC2 t2.medium | Ubuntu 22.04 LTS |
| PII data generation | Python Faker | Generate realistic test data |

---

## Prerequisites

### Local Machine
- Docker Desktop installed and running
- Python 3.10 or higher
- PowerShell or CMD (Windows) / Terminal (Mac/Linux)

### AWS Account
- IAM user with `AmazonS3FullAccess` policy
- Access Key ID and Secret Access Key
- Two S3 buckets created in `ap-south-1` region:
  - `dsmp-email-metadata`
  - `dsmp-chat-metadata`

### EC2 Server
- Ubuntu Server 22.04 LTS (plain — no SQL Server)
- Instance type: t2.medium recommended (t2.small minimum)
- Security Group inbound rules:
  - Port 22 (SSH)
  - Port 8025 (MailHog UI)
  - Port 8065 (Mattermost)

---

## Project Structure

```
dsmp-aws-pipeline/
├── config.py                 # All connection settings
├── push_to_s3.py             # AWS S3 upload / list / download helpers
├── extract_mailhog.py        # Pull emails from MailHog → push to S3
├── extract_mattermost.py     # Pull chat posts from Mattermost → push to S3
├── run_pipeline.py           # Main orchestrator — runs full pipeline
├── debug_mattermost.py       # Debug script to test Mattermost connection
└── venv/                     # Python virtual environment

mattermost-dsmp/
└── docker-compose.yml        # Mattermost + PostgreSQL containers
```

---

## Setup Guide

### 1. Local Development Setup

#### Start Docker Containers

Create `mattermost-dsmp/docker-compose.yml`:

```yaml
version: "3.9"
services:
  postgres:
    image: postgres:15
    container_name: mattermost-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: mmuser
      POSTGRES_PASSWORD: mmpassword
      POSTGRES_DB: mattermost
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mmuser -d mattermost"]
      interval: 10s
      timeout: 5s
      retries: 5

  mattermost:
    image: mattermost/mattermost-team-edition
    container_name: mattermost
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "8065:8065"
    environment:
      MM_SQLSETTINGS_DRIVERNAME: postgres
      MM_SQLSETTINGS_DATASOURCE: postgres://mmuser:mmpassword@postgres:5432/mattermost?sslmode=disable
      MM_SERVICESETTINGS_SITEURL: http://localhost:8065
      MM_TEAMSETTINGS_ENABLEOPENSERVER: "true"
    volumes:
      - mattermost_data:/mattermost/data

volumes:
  postgres_data:
  mattermost_data:
```

Start Mattermost:
```bash
cd mattermost-dsmp
docker compose up -d
```

Start MailHog:
```bash
docker run -d --name mailhog -p 1025:1025 -p 8025:8025 mailhog/mailhog
```

#### Configure Mattermost

1. Open `http://localhost:8065`
2. Create admin account
3. Create team: `DSMP Test Team`
4. Create channel: `#general-data`
5. Add team members via System Console

#### Generate Dummy Test Data

Install dependencies:
```bash
pip install faker boto3 requests
```

Send dummy emails with PII to MailHog:
```python
import smtplib
from email.mime.text import MIMEText

msg = MIMEText("Aadhaar: 3456 7890 1234 | PAN: ABCDE1234F | Salary: Rs.24L")
msg['Subject'] = "Payroll Details - Confidential"
msg['From'] = "hr@dsmp-corp.io"
msg['To'] = "rahul.sharma@dsmp-corp.io"

s = smtplib.SMTP('localhost', 1025)
s.send_message(msg)
s.quit()
```

---

### 2. AWS Setup

#### Create IAM User

1. Go to AWS Console → IAM → Users → Create User
2. Username: `dsmp-s3-user`
3. Attach policy: `AmazonS3FullAccess`
4. Create Access Key → select Local code → copy both keys

#### Create S3 Buckets

Go to AWS Console → S3 → Create bucket:

```
Bucket 1: dsmp-email-metadata   Region: ap-south-1
Bucket 2: dsmp-chat-metadata    Region: ap-south-1
Block all public access: ON
```

#### Configure Pipeline

Edit `config.py`:

```python
# ── MailHog ───────────────────────────────────────
MAILHOG_API   = "http://localhost:8025/api/v2/messages"
MAILHOG_LIMIT = 50

# ── Mattermost ────────────────────────────────────
MM_BASE_URL = "http://localhost:8065/api/v4"
MM_USERNAME = "your_admin_username"
MM_PASSWORD = "your_admin_password"

# ── AWS S3 ────────────────────────────────────────
AWS_ACCESS_KEY = "AKIAxxxxxxxxxxxxxxxxx"
AWS_SECRET_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
AWS_REGION     = "ap-south-1"

# ── Bucket Names ──────────────────────────────────
BUCKET_EMAIL = "dsmp-email-metadata"
BUCKET_CHAT  = "dsmp-chat-metadata"
```

> **Security Note:** Never commit `config.py` to Git. Add it to `.gitignore`. Use environment variables in production.

---

### 3. Server Deployment (AWS EC2)

#### Launch EC2 Instance

- AMI: Ubuntu Server 22.04 LTS (plain — no SQL Server)
- Instance type: t2.medium
- Key pair: create new → download `.pem` file
- Security Group: open ports 22, 8025, 8065

#### Connect to Server

```bash
ssh -i /path/to/dsmp-key.pem ubuntu@YOUR_EC2_IP
```

#### Install Docker on Server

```bash
sudo apt update -y
sudo apt install -y ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update -y
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu
newgrp docker
```

#### Install Python

```bash
sudo apt install -y python3 python3-pip python3-venv python3-full
```

#### Copy Files to Server

From your local PowerShell:
```powershell
# Create folders on server first
ssh -i C:\path\to\dsmp-key.pem ubuntu@YOUR_EC2_IP "mkdir -p /home/ubuntu/mattermost-dsmp && mkdir -p /home/ubuntu/dsmp-aws-pipeline"

# Copy docker-compose
scp -i C:\path\to\dsmp-key.pem C:\mattermost-dsmp\docker-compose.yml ubuntu@YOUR_EC2_IP:/home/ubuntu/mattermost-dsmp/docker-compose.yml

# Copy pipeline files
scp -i C:\path\to\dsmp-key.pem C:\dsmp-aws-pipeline\config.py ubuntu@YOUR_EC2_IP:/home/ubuntu/dsmp-aws-pipeline/config.py
scp -i C:\path\to\dsmp-key.pem C:\dsmp-aws-pipeline\push_to_s3.py ubuntu@YOUR_EC2_IP:/home/ubuntu/dsmp-aws-pipeline/push_to_s3.py
scp -i C:\path\to\dsmp-key.pem C:\dsmp-aws-pipeline\extract_mailhog.py ubuntu@YOUR_EC2_IP:/home/ubuntu/dsmp-aws-pipeline/extract_mailhog.py
scp -i C:\path\to\dsmp-key.pem C:\dsmp-aws-pipeline\extract_mattermost.py ubuntu@YOUR_EC2_IP:/home/ubuntu/dsmp-aws-pipeline/extract_mattermost.py
scp -i C:\path\to\dsmp-key.pem C:\dsmp-aws-pipeline\run_pipeline.py ubuntu@YOUR_EC2_IP:/home/ubuntu/dsmp-aws-pipeline/run_pipeline.py
```

#### Start Containers on Server

```bash
cd /home/ubuntu/mattermost-dsmp
docker compose up -d
docker run -d --name mailhog -p 1025:1025 -p 8025:8025 mailhog/mailhog
docker ps
```

#### Setup Python Virtual Environment

```bash
cd /home/ubuntu/dsmp-aws-pipeline
python3 -m venv venv
source venv/bin/activate
pip install boto3 requests
```

---

## Running the Pipeline

#### Manual Run

```bash
cd /home/ubuntu/dsmp-aws-pipeline
source venv/bin/activate
python3 run_pipeline.py
```

Expected output:
```
============================================================
  DSMP — MailHog + Mattermost  →  AWS S3
============================================================
📨 Extracting emails from MailHog → AWS S3...
   Found 26 emails
  ✅ Uploaded → s3://dsmp-email-metadata/emails/abc123.json
  ✅ Uploaded → s3://dsmp-email-metadata/summary/all_emails.json
💬 Extracting messages from Mattermost → AWS S3...
  ✅ Uploaded → s3://dsmp-chat-metadata/posts/general-data/xyz.json
  ✅ Uploaded → s3://dsmp-chat-metadata/summary/all_messages.json
============================================================
  ✅ PIPELINE COMPLETE
============================================================
  Emails pushed    : 26
  Messages pushed  : 12
============================================================
```

---

## Scheduling

Set pipeline to run automatically every 15 minutes:

```bash
crontab -e
```

Add this line:
```bash
*/15 * * * * cd /home/ubuntu/dsmp-aws-pipeline && source venv/bin/activate && python3 run_pipeline.py >> /home/ubuntu/dsmp.log 2>&1
```

#### Schedule Options

| Frequency | Cron Expression |
|---|---|
| Every 15 minutes | `*/15 * * * *` |
| Every 30 minutes | `*/30 * * * *` |
| Every hour | `0 * * * *` |
| Every day at 9am | `0 9 * * *` |

---

## Monitoring

#### Check Log
```bash
tail -f /home/ubuntu/dsmp.log
```

#### Check Containers
```bash
docker ps
```

#### Check S3 Files
```bash
cd /home/ubuntu/dsmp-aws-pipeline
source venv/bin/activate
python3 -c "
from push_to_s3 import list_files
from config import BUCKET_EMAIL, BUCKET_CHAT
list_files(BUCKET_EMAIL)
list_files(BUCKET_CHAT)
"
```

#### All-in-One Health Check
```bash
echo "=== CRON ===" && crontab -l && echo "=== CONTAINERS ===" && docker ps --format "table {{.Names}}\t{{.Status}}" && echo "=== LAST 10 LOG LINES ===" && tail -10 /home/ubuntu/dsmp.log
```

---

## Security

- Never commit `config.py` or any file containing AWS keys to Git
- Add `config.py` to `.gitignore`
- Use environment variables in production:

```bash
export AWS_ACCESS_KEY="AKIAxxxxx"
export AWS_SECRET_KEY="xxxxxxxxx"
```

```python
import os
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_KEY")
```

- Rotate AWS keys regularly
- Keep EC2 Security Group restricted to your IP only for ports 8025 and 8065
- Enable S3 bucket versioning for audit trail

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `InvalidAccessKeyId` | Wrong AWS key in config.py | Update with correct key from IAM console |
| `AccessDenied on S3` | Missing S3 policy | Attach `AmazonS3FullAccess` to IAM user |
| `401 Invalid credentials` | Wrong Mattermost password | Check credentials at `http://EC2_IP:8065` |
| `Connection refused 8065` | Mattermost not running | Run `docker compose up -d` |
| `Connection refused 8025` | MailHog not running | Run `docker run -d --name mailhog ...` |
| `string indices must be integers` | Mattermost login failed | Fix credentials in config.py |
| `externally-managed-environment` | Ubuntu pip restriction | Use `python3 -m venv venv` |
| `bad permissions .pem` | Key file too open | Run `icacls` permission fix or use PuTTY |
| `dest open Failure` on scp | Folder doesn't exist on server | Run `mkdir -p` on server first |

---

## Data Flow Summary

```
MailHog (emails)
    └── REST API → extract_mailhog.py
            └── metadata JSON → push_to_s3.py
                    └── s3://dsmp-email-metadata/
                            ├── emails/{id}.json
                            └── summary/all_emails.json

Mattermost (chat)
    └── REST API → extract_mattermost.py
            └── metadata JSON → push_to_s3.py
                    └── s3://dsmp-chat-metadata/
                            ├── posts/{channel}/{id}.json
                            └── summary/all_messages.json
```

---

## Next Steps

- Add NLP pipeline using **spaCy + Microsoft Presidio** for PII detection
- Add risk scoring engine with weighted entity scoring
- Connect findings to **Grafana** dashboard for visualisation
- Add **Apache Airflow** for advanced pipeline orchestration
- Extend to additional sources: MinIO documents, Gitea code repositories

---

## Author

Built for the DSMP (Data Security Management Platform) project.
For dev/test use only — all data sources are synthetic.
