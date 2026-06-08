from extract_mailhog    import extract_mailhog
from extract_mattermost import extract_mattermost
from push_to_s3         import list_files
from config             import BUCKET_EMAIL, BUCKET_CHAT

print("=" * 60)
print("  DSMP — MailHog + Mattermost  →  AWS S3")
print("=" * 60)

# Run both extractors
email_data = extract_mailhog()
chat_data  = extract_mattermost()

# Show what landed in S3
print("\n" + "=" * 60)
print("  📦 FILES NOW IN AWS S3")
print("=" * 60)
list_files(BUCKET_EMAIL)
list_files(BUCKET_CHAT)

# Final summary
print("\n" + "=" * 60)
print("  ✅ PIPELINE COMPLETE")
print("=" * 60)
print(f"  Emails pushed    : {len(email_data)}")
print(f"  Messages pushed  : {len(chat_data)}")
print(f"\n  Check S3 console:")
print(f"  https://s3.console.aws.amazon.com/s3/buckets/dsmp-email-metadata")
print(f"  https://s3.console.aws.amazon.com/s3/buckets/dsmp-chat-metadata")
print("=" * 60)