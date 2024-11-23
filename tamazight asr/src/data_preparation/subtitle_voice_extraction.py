import requests
import websocket
import json
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

load_dotenv()

API_URL = 'https://subtitleextractor.com/api/v1'
WS_URL = 'wss://api.subtitleextractor.com/updates'
API_KEY = os.getenv('SUBTITLE_EXTRACTOR_API_KEY')

# Step 1: Get a presigned URL for uploading
def get_presigned_url():
    response = requests.post(f"{API_URL}/upload/file", 
                           headers={'Authorization': f'Bearer {API_KEY}'})
    return response.json()

# Step 2: Upload the file directly to S3 using the presigned URL
def upload_file(file_path, upload_url):
    with open(file_path, 'rb') as file:
        response = requests.put(upload_url, 
                              data=file,
                              headers={'Content-Type': 'application/octet-stream'})
    return response.status_code

# Step 3: Create a subtitle extraction
def create_extraction(upload_id):
    response = requests.post(f"{API_URL}/extract",
                           json={
                               'method': 'vision',  # or 'vision', adjust as necessary
                               'uploadId': upload_id,
                               'language': 'Auto-Detect'
                           },
                           headers={'Authorization': f'Bearer {API_KEY}'})
    response_data = response.json()
    
    # Add response validation
    if response.status_code != 200:
        print(response_data)
        raise Exception(f"Extraction creation failed: {response_data.get('message', 'Unknown error')}")
    
    extraction_id = response_data.get('id')
    if not extraction_id:
        raise Exception("No extraction ID received in response")
        
    return response_data

# Step 4: Connect to WebSocket and listen for extraction completion
def on_message(ws, message):
    message = json.loads(message)
    if message.get('type') == 'status' and message.get('status') == 'SUCCEEDED':
        print(f"Extraction completed. SRT URL: {message['outputUrl']}")
        ws.close()
        download_srt(message['outputUrl'])

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket connection closed")

def listen_to_websocket(extraction_id):
    ws = websocket.WebSocketApp(
        f"{WS_URL}?token={API_KEY}",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    def on_open(ws):
        ws.send(json.dumps({'action': 'subscribe', 'jobId': extraction_id}))
    
    ws.on_open = on_open
    ws.run_forever()

# Step 5: Download the SRT file
def download_srt(srt_url):
    response = requests.get(srt_url, stream=True)
    with open('subtitle.srt', 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print('Download completed.')

def run_process(file_path):
    try:
        presigned_data = get_presigned_url()
        upload_url = presigned_data.get('uploadUrl')
        upload_id = presigned_data.get('uploadId')
        
        if not upload_url or not upload_id:
            raise Exception("Invalid presigned URL response")
        
        upload_status = upload_file(file_path, upload_url)
        if upload_status != 200:
            raise Exception(f"File upload failed with status {upload_status}")
            
        extraction_data = create_extraction(upload_id)
        extraction_id = extraction_data['id']
        
        listen_to_websocket(extraction_id)
    except Exception as error:
        logging.error(f'Error: {str(error)}', exc_info=True)
        
if __name__ == '__main__':
    path = r'C:\Users\Soufiane.DAHIMI\Projects\ML & DL\Tamazight ASR\tamazight asr\prototyping\cropped_video.mp4'
    run_process(path)