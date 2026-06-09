import requests
from datetime import datetime
from config      import MM_BASE_URL, MM_USERNAME, MM_PASSWORD, BUCKET_CHAT
from push_to_s3  import upload_json

def login():
    resp  = requests.post(f"{MM_BASE_URL}/users/login",
                json={"login_id": MM_USERNAME, "password": MM_PASSWORD})
    token = resp.headers.get("Token")
    print(f"  ✅ Mattermost login success")
    return token

def extract_mattermost():
    print("\n💬 Extracting messages from Mattermost → AWS S3...\n")

    TOKEN   = login()
    HEADERS = {"Authorization": f"Bearer {TOKEN}"}

    # Get all teams
    teams = requests.get(f"{MM_BASE_URL}/teams", headers=HEADERS).json()
    print(f"   Found {len(teams)} team(s)\n")

    all_messages = []

    for team in teams:
        team_id   = team["id"]
        team_name = team["display_name"]
        print(f"   📁 Team: {team_name}")

        # Get all channels
        channels = requests.get(
            f"{MM_BASE_URL}/teams/{team_id}/channels",
            headers=HEADERS
        ).json()

        for channel in channels:
            channel_id   = channel["id"]
            channel_name = channel.get("display_name",
                           channel.get("name", "unknown"))
            print(f"      # {channel_name}")

            # Get posts in channel
            posts_resp = requests.get(
                f"{MM_BASE_URL}/channels/{channel_id}/posts?per_page=50",
                headers=HEADERS
            ).json()

            posts = posts_resp.get("posts", {})
            order = posts_resp.get("order", [])

            for post_id in order:
                post    = posts.get(post_id, {})
                user_id = post.get("user_id", "")

                # Get sender details
                user     = requests.get(
                    f"{MM_BASE_URL}/users/{user_id}",
                    headers=HEADERS
                ).json()
                username = user.get("username", "unknown")
                email    = user.get("email", "")

                # Build metadata
                metadata = {
                    "source"         : "mattermost",
                    "post_id"        : post_id,
                    "team_id"        : team_id,
                    "team_name"      : team_name,
                    "channel_id"     : channel_id,
                    "channel_name"   : channel_name,
                    "user_id"        : user_id,
                    "username"       : username,
                    "user_email"     : email,
                    "message"        : post.get("message", ""),
                    "message_length" : len(post.get("message", "")),
                    "has_files"      : len(post.get("file_ids", [])) > 0,
                    "file_count"     : len(post.get("file_ids", [])),
                    "create_at"      : post.get("create_at", ""),
                    "extracted_at"   : datetime.utcnow().isoformat()
                }

                all_messages.append(metadata)

                # Push each post to S3
                upload_json(
                    BUCKET_CHAT,
                    f"posts/{channel_name}/{post_id}.json",
                    metadata
                )

    # Push combined summary
    upload_json(BUCKET_CHAT, "summary/all_messages.json", {
        "total"        : len(all_messages),
        "extracted_at" : datetime.utcnow().isoformat(),
        "source"       : "mattermost",
        "messages"     : all_messages
    })

    print(f"\n✅ Mattermost done — {len(all_messages)} messages pushed to s3://{BUCKET_CHAT}")
    return all_messages


if __name__ == "__main__":
    extract_mattermost()