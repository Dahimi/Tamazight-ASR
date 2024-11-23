import pysrt
import moviepy as mp
from pydub import AudioSegment
import os
import pandas as pd
def parse_srt(srt_path):
    """
    Parse SRT file and return list of subtitle entries with timestamps
    """
    subs = pysrt.open(srt_path)
    subtitle_data = []
    
    for sub in subs:
        # Convert timestamps to seconds
        start_time = sub.start.hours * 3600 + sub.start.minutes * 60 + sub.start.seconds + sub.start.milliseconds / 1000
        end_time = sub.end.hours * 3600 + sub.end.minutes * 60 + sub.end.seconds + sub.end.milliseconds / 1000
        
        subtitle_data.append({
            'text': sub.text.strip(),
            'start_time': start_time,
            'end_time': end_time,
            'duration': end_time - start_time
        })
    
    return subtitle_data


def extract_audio_segments(video_path, subtitle_data, output_dir="audio_segments"):
    """
    Extract audio segments corresponding to each subtitle
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract audio from video
    video = mp.VideoFileClip(video_path)
    audio = video.audio
    
    # Save full audio temporarily
    temp_audio_path = "temp_audio.wav"
    audio.write_audiofile(temp_audio_path)
    
    # Load audio file using pydub
    full_audio = AudioSegment.from_wav(temp_audio_path)
    
    segments = []
    for idx, sub in enumerate(subtitle_data):
        # Convert timestamps to milliseconds
        start_ms = sub['start_time'] * 1000
        end_ms = sub['end_time'] * 1000
        
        # Extract segment
        segment = full_audio[start_ms:end_ms]
        
        # Generate output filename
        output_file = os.path.join(output_dir, f"segment_{idx:04d}.wav")
        
        # Export segment
        segment.export(output_file, format="wav")
        
        segments.append({
            'text': sub['text'],
            'audio_path': output_file,
            'start_time': sub['start_time'],
            'end_time': sub['end_time'],
            'duration': sub['duration']
        })
    
    # Cleanup
    os.remove(temp_audio_path)
    video.close()
    
    return segments


def create_dataset(segments, output_path):
    """
    Create a CSV file with audio paths and corresponding text, appending if file exists
    """
    df = pd.DataFrame(segments)
    if os.path.exists(output_path):
        existing_df = pd.read_csv(output_path)
        df = pd.concat([existing_df, df], ignore_index=True)
    df.to_csv(output_path, index=False)
    return df

def process_video_and_srt(video_path, srt_path, output_dir="C:/Users/Soufiane.DAHIMI/Projects/ML & DL/Tamazight ASR/tamazight_asr/data/"):
    """
    Main function to process video and SRT file
    """
    # Parse SRT file
    print("Parsing SRT file...")
    subtitle_data = parse_srt(srt_path)
    
    # Extract audio segments
    print("Extracting audio segments...")
    segments = extract_audio_segments(video_path, subtitle_data, 
                                    output_dir=os.path.join(output_dir, "audios"))
    
    # Create dataset file
    print("Creating dataset file...")
    dataset = create_dataset(segments, 
                           output_path=os.path.join(output_dir, "dataset.csv"))
    
    return dataset

if __name__ == "__main__":
    video_path = r'C:\Users\Soufiane.DAHIMI\Projects\ML & DL\Tamazight ASR\tamazight_asr\data\videos\output_video.mp4'
    srt_path = r'C:\Users\Soufiane.DAHIMI\Projects\ML & DL\Tamazight ASR\tamazight_asr\data\srt\output_video.srt'
    process_video_and_srt(video_path, srt_path)
