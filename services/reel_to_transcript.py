import assemblyai as aai
import requests
import instaloader
import os
from openai import OpenAI
from flask import jsonify

def download_reel(reel_url, output_dir="None"):
    print("VERCEL",os.getenv('VERCEL'))
    if os.getenv('VERCEL'):
        # Use Vercel's writable temporary directory
        output_dir = '/tmp/reels'
    else:
        # Use the specified local directory or default to 'reels'
        output_dir = output_dir or 'reels'
        os.makedirs(output_dir, exist_ok=True)

    # Initialize Instaloader with the specified output directory
    loader = instaloader.Instaloader(dirname_pattern=output_dir)

    # Extract the shortcode from the URL
    base_url = reel_url.split('?')[0]
    # Split the URL and get the last non-empty segment
    shortcode = base_url.rstrip('/').split('/')[-1]
    print("shortcode",shortcode)

    # Download the reel
    try:
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        loader.download_post(post, target=output_dir)
        # Find the downloaded .mp4 file
        for file in os.listdir(output_dir):
            if file.endswith(".mp4"):
                video_path = os.path.join(output_dir, file)
                return video_path
            
    except Exception as e:
        print(f"Error downloading reel: {e}")
        return None


def rewrite_transcript(org_transcript):

    client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY')
    )

    default_prompt = """
        Using the information in the transcript above, write a script for an
        educational and informative 1-minute video. Keep in mind that the video script will be read out loud and not shown on the screen.
        The script should follow the following format:
        • Hook
        • Describe the problem in more detail
        • Discuss the solution
        • Give more detail or examples of the solution.
        • Call to action
        Total script should be a maximum of 120 words with an extremely conversational tone and casual word choice.
        """
    combined_prompt = f"{default_prompt}\n\nTranscript:\n{org_transcript}"

    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": combined_prompt}]
    )

    response_message = response.choices[0].message.content.strip()
    print("response_message", response_message)

    
    return response_message


def processVideo(reel_url):
    video_path = download_reel(reel_url)

    aai.settings.api_key = os.getenv('ASSEMBLE_API_KEY')
    aai.settings.http_timeout = 120

    print(video_path, "video_path")
    transcriber = aai.Transcriber()
    try:
        # Transcribe the video file
        transcript = transcriber.transcribe(video_path)
        
        if transcript.status == aai.TranscriptStatus.error:
            print("Error during transcription:", transcript.error)
            return jsonify({'error': 'Transcription failed', 'details': transcript.error})
        else:
            print("Transcript:", transcript.text)
            re_trans = rewrite_transcript(transcript.text)
            print("Rewritten:", re_trans)
            
            return jsonify({'transcript': transcript.text, 'rewritten_transcript': re_trans})
    
    finally:
        # Cleanup the temporary directory after processing
        tmp_dir = os.getenv('VERCEL') and '/tmp/reels' or None
        if tmp_dir:
            try:
                for temp_file in os.listdir(tmp_dir):
                    temp_file_path = os.path.join(tmp_dir, temp_file)
                    os.remove(temp_file_path)
                print("Temporary directory cleaned up.")
            except Exception as cleanup_error:
                print(f"Error cleaning up temporary directory: {cleanup_error}")

