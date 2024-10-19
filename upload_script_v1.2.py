import os
import google.auth
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
from datetime import datetime

# You need to replace these with your own values
CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl"]  # To manage playlists

# Authenticate and initialize the YouTube API
def get_authenticated_service():
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_local_server(port=0)
    return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

# Upload video to YouTube
def upload_video(youtube, video_file, title, description, category, tags):
    request_body = {
        "snippet": {
            "categoryId": category,
            "description": description,
            "title": title,
            "tags": tags,
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": "public",  # or "private", "unlisted"
            "selfDeclaredMadeForKids": False  # Mark as "No, it's not made for kids"
        }
    }

    media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media
    )

    response = request.execute()
    print(f"Video uploaded successfully! Video ID: {response['id']}")
    return response['id']

# Create a new playlist
def create_playlist(youtube, title, description):
    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "defaultLanguage": "en"
        },
        "status": {
            "privacyStatus": "public"
        }
    }
    
    response = youtube.playlists().insert(
        part="snippet,status",
        body=request_body
    ).execute()
    
    print(f"Playlist created successfully! Playlist ID: {response['id']}")
    return response['id']

# Add video to playlist
def add_video_to_playlist(youtube, playlist_id, video_id):
    request_body = {
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {
                "kind": "youtube#video",
                "videoId": video_id
            }
        }
    }

    response = youtube.playlistItems().insert(
        part="snippet",
        body=request_body
    ).execute()
    
    print(f"Added video {video_id} to playlist {playlist_id}")

# Rename video files and upload them to YouTube
def process_videos(youtube, video_files, match_date):
    # Create playlist with the format "Matchday Football DD/MM/YY"
    playlist_title = f"Matchday Football {match_date.strftime('%d/%m/%y')}"
    playlist_id = create_playlist(youtube, playlist_title, "Football match playlist")

    for i, video_file in enumerate(video_files, start=1):
        # Rename video with format "DD/MM/YY Part X"
        new_filename = os.path.join(os.path.dirname(video_file), f"{match_date.strftime('%d-%m-%y')} Part {i}.mp4")
        os.rename(video_file, new_filename)

        # Upload video
        title = f"{match_date.strftime('%d/%m/%y')} Part {i}"
        video_id = upload_video(youtube, new_filename, title, "Football match footage", "17", ["football", "matchday"])

        # Add the video to the playlist
        add_video_to_playlist(youtube, playlist_id, video_id)

# Get all video files from the directory
def get_video_files_from_directory(directory):
    # List all files in the directory with .mp4 extension
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".mp4")]

if __name__ == "__main__":
    # Path to the directory containing the videos
    video_directory = "E:\\Video\\"  # Replace with your directory
    
    # Get all .mp4 video files from the specified directory
    video_files = get_video_files_from_directory(video_directory)

    # Date of the match (modify according to the actual match date)
    match_date = datetime.strptime("2024-10-19", "%Y-%m-%d")  # Replace with your match date
    
    # Authenticate and initialize the YouTube API
    youtube = get_authenticated_service()
    
    # Process the videos: rename, upload, and add to playlist
    process_videos(youtube, video_files, match_date)
