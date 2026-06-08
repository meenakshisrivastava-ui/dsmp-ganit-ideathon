import boto3
import json
from datetime import datetime
from config import (AWS_ACCESS_KEY, AWS_SECRET_KEY,
                    AWS_REGION)

# Connect to real AWS S3
s3 = boto3.client(
    "s3",
    region_name          = AWS_REGION,
    aws_access_key_id    = AWS_ACCESS_KEY,
    aws_secret_access_key= AWS_SECRET_KEY,
)

def upload_json(bucket, filename, data):
    """Upload a Python dict as JSON to AWS S3"""
    content = json.dumps(data, indent=2, default=str)

    s3.put_object(
        Bucket      = bucket,
        Key         = filename,
        Body        = content.encode("utf-8"),
        ContentType = "application/json"
    )
    print(f"  ✅ Uploaded → s3://{bucket}/{filename}")


def list_files(bucket):
    """List all files inside an S3 bucket"""
    resp  = s3.list_objects_v2(Bucket=bucket)
    files = resp.get("Contents", [])

    print(f"\n📦 Files in s3://{bucket}")
    if not files:
        print("   (empty)")
    for f in files:
        size = round(f['Size'] / 1024, 2)
        print(f"   {f['Key']:<55} {size} KB")
    return files


def download_json(bucket, filename):
    """Download and return a JSON file from S3"""
    obj  = s3.get_object(Bucket=bucket, Key=filename)
    data = json.loads(obj["Body"].read().decode("utf-8"))
    return data