import requests
from datetime import datetime
from config       import MAILHOG_API, MAILHOG_LIMIT, BUCKET_EMAIL
from push_to_s3   import upload_json

def extract_mailhog():
    print("\n📨 Extracting emails from MailHog → AWS S3...\n")

    # Pull from MailHog REST API
    resp   = requests.get(f"{MAILHOG_API}?limit={MAILHOG_LIMIT}")
    emails = resp.json().get("items", [])
    print(f"   Found {len(emails)} emails\n")

    all_metadata = []

    for idx, email in enumerate(emails):

        # ── Parse fields ────────────────────────────────
        msg_id   = email.get("ID", f"msg_{idx}")
        from_obj = email.get("From", {})
        to_list  = email.get("To", [])
        headers  = email.get("Content", {}).get("Headers", {})
        body     = email.get("Content", {}).get("Body", "")

        from_addr = f"{from_obj.get('Mailbox','')}@{from_obj.get('Domain','')}"
        to_addrs  = [f"{t.get('Mailbox','')}@{t.get('Domain','')}" for t in to_list]
        subject   = headers.get("Subject",  ["(no subject)"])[0]
        date      = headers.get("Date",     [""])[0]
        mime_type = headers.get("Content-Type", ["text/plain"])[0]

        # ── Build metadata ──────────────────────────────
        metadata = {
            "source"         : "mailhog",
            "message_id"     : msg_id,
            "from"           : from_addr,
            "to"             : to_addrs,
            "to_count"       : len(to_addrs),
            "subject"        : subject,
            "date"           : date,
            "mime_type"      : mime_type,
            "body"           : body,
            "body_length"    : len(body),
            "has_attachment" : "multipart" in mime_type.lower(),
            "extracted_at"   : datetime.utcnow().isoformat()
        }

        all_metadata.append(metadata)

        # ── Push each email to S3 ───────────────────────
        upload_json(BUCKET_EMAIL, f"emails/{msg_id}.json", metadata)

    # ── Push combined summary ───────────────────────────
    upload_json(BUCKET_EMAIL, "summary/all_emails.json", {
        "total"        : len(all_metadata),
        "extracted_at" : datetime.utcnow().isoformat(),
        "source"       : "mailhog",
        "emails"       : all_metadata
    })

    print(f"\n✅ MailHog done — {len(emails)} emails pushed to s3://{BUCKET_EMAIL}")
    return all_metadata


if __name__ == "__main__":
    extract_mailhog()