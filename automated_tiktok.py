import os
from gtts import gTTS
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
import yt_dlp  # Updated import for yt-dlp
from google.cloud import texttospeech
import google.generativeai as genai
from moviepy import VideoFileClip, concatenate_videoclips
import azure.cognitiveservices.speech as speechsdk
import random
import openai
import requests

# Your Pixabay API key
API_KEY = 'your key'
AZURE_CHAT_KEY='your key'

# Step 1: Download a Copyright-Free Space Video
def download_space_video(url, output_file):
    print("Downloading space video...")
    
    ydl_opts = {
        'format': 'best',  # Download best quality video
        'outtmpl': output_file,  # Specify the output file
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    
    
    print("Video downloaded successfully!")
    

def createBGVideo(output_file):
    global topic 
    
    folder_path = '/Users/jotham/Desktop/Code/stock1'  # Replace with your folder path
    folder_path='/Users/jotham/Desktop/Code/downloaded_videos'
    
    print(topic)
    downloadStockFootage(topic)

    # Get a list of video files in the folder (you can filter by .mp4 or other formats)
    video_files = [f for f in os.listdir(folder_path) if f.endswith(('.mp4', '.mov', '.avi'))]

    # Randomly select a few videos (e.g., 5) from the folder
    num_videos_to_cut = 12  # Change this to select more or fewer videos
    selected_videos = random.sample(video_files, num_videos_to_cut)

    # Desired output resolution for vertical videos
    output_width = 1080
    output_height = 1920  # Standard vertical resolution (9:16 aspect ratio)

    # List to store video clips after cutting and resizing
    clips = []

    # Process each video file
    for video_file in selected_videos:
        video_path = os.path.join(folder_path, video_file)
        clip = VideoFileClip(video_path)

        # Check if the video is long enough to cut (at least 10 seconds)
        if clip.duration > 5:
            # Cut the video to a random segment (10 seconds)
            start_time = random.randint(0, int(clip.duration - 5))  # Random start time
            end_time = start_time + 5  # End time (10 seconds after start time)
            cut_clip = clip.subclipped(start_time, end_time)
            
            vertical_size = (1080, 1920)  # Define your desired vertical resolutions
            cut_clip = cut_clip.resized(vertical_size)


            clips.append(cut_clip)
        else:
            print(f"Video {video_file} is too short, skipping...")

    # Concatenate the clips into one video
    if clips:
        # Concatenate clips
        final_clip = concatenate_videoclips(clips, method="compose")

        # Save the final video
        #output_path = 'output_video_vertical.mp4'  # Path where the final video will be saved
        final_clip.write_videofile(output_file, codec="libx264", fps=30)

        print(f"Vertical video created successfully! Saved as {output_file}")
    else:
        print("No valid video clips found to combine.")


def downloadStockFootage(query):
    
    search="space "+query
    print(search)
    
    url = f"https://pixabay.com/api/videos/?key={API_KEY}&q={search}&per_page=14"
    response = requests.get(url)
    data = response.json()
    download_folder="downloaded_videos"

    if 'hits' in data and len(data['hits']) > 0:
        for index, hit in enumerate(data['hits']):
            # Use 'large' for the highest available quality
            video_url = hit['videos']['large']['url']
            video_response = requests.get(video_url, stream=True)
            
            # Save each video with a unique filename
            download_path = f"{download_folder}/video_{index + 1}.mp4"
            with open(download_path, 'wb') as file:
                for chunk in video_response.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)
            print(f"Video {index + 1} downloaded successfully: {download_path}")
    else:
        print("No videos found.")
    

# Step 2: Generate the Voiceover
def generate_voiceover(script_text, output_audio_file):

    speech_key = "your key"
    service_region = "eastus"


    if not speech_key or not service_region:
        raise ValueError("API key or region is missing. Set them as environment variables.")

    # Create the Speech Config
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

    # Choose a narratorial voice
    speech_config.speech_synthesis_voice_name = "en-GB-RyanNeural"  # Replace with your preferred voice

    # Configure output file
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_audio_file)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    # Use SSML for narration style
    narration_ssml = f"""
    <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
        <voice name='en-GB-RyanNeural'>
            <prosody pitch='-10%' rate='0.85'>
            {script_text}
            </prosody>
        </voice>
    </speak>
    """

    # Generate TTS audio
    result = synthesizer.speak_ssml_async(narration_ssml).get()
    

def generate_google_cloud_voiceover(script_text, output_audio_file):
    # Initialize the Google Cloud TTS client
    client = texttospeech.TextToSpeechClient()

    # Configure the voice request (e.g., choose a specific voice, language, and SSML)
    synthesis_input = texttospeech.SynthesisInput(text=script_text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", 
        name="en-US-Wavenet-D"  # Wavenet voices are more natural
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Make the request
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    # Write the audio to the output file
    with open(output_audio_file, "wb") as out:
        out.write(response.audio_content)
    
    print(f"Voiceover saved to {output_audio_file}")

# Example usage


def create_subtitle_clips_dynamically(script_text, audio_file, video_size, font_size=95, font_color="yellow", border_color="black", stroke_width=6):
    print("Creating subtitles...")
    words = script_text.split()
    words_per_frame = 3
    word_groups = [' '.join(words[i:i + words_per_frame]) for i in range(0, len(words), words_per_frame)]

    # Analyze audio timing
    audio_clip = AudioFileClip(audio_file)
    audio_duration = audio_clip.duration

    # Calculate duration per subtitle
    duration_per_group = audio_duration / len(word_groups)
    subtitle_clips = []

    for i, group in enumerate(word_groups):
        start_time = i * duration_per_group
        end_time = start_time + duration_per_group

        # Create the subtitle with styles
        subtitle = TextClip(
            text=group,
            font="Arial",
            font_size=font_size,
            color=font_color,
            stroke_color=border_color,
            stroke_width=stroke_width,
            size=(video_size[0], None),
        ).with_position(("center", video_size[1] - 450))  # Adjust the position

        subtitle = subtitle.with_duration(duration_per_group).with_start(start_time)
        subtitle_clips.append(subtitle)

    print("Subtitles created dynamically!")
    return subtitle_clips




# Step 3: Create Subtitles (2 words at a time)
def create_subtitle_clips(script_text, audio_duration, video_size, font_size=95, font_color="yellow", border_color="black", stroke_width=6):
    print("Creating subtitles...")
    words = script_text.split()
    wordsPerFrame=3
    word_pairs = [' '.join(words[i:i+wordsPerFrame]) for i in range(0, len(words), wordsPerFrame)]  # 2 words per line
    
    # Adjust the subtitle duration based on the audio duration and number of word pairs
    duration_per_line = audio_duration / len(word_pairs)
    subtitle_clips = []
    
    # Vertically center the text
    y_position = video_size[1] // 2  # Center vertically (half the video height)

    for i, pair in enumerate(word_pairs):
        start_time = i * duration_per_line
        end_time = start_time + duration_per_line
        
        # Create the subtitle with yellow text and black border
        subtitle = TextClip(
            text=pair,
            font="Arial",  # Ensure this is a valid font on your system
            font_size=font_size,
            color=font_color,
            stroke_color=border_color,  # Border color (black)
            stroke_width=stroke_width,  # Border width
            size=(video_size[0], None),  # Full width of the video
        )
        
        # Adjust vertical positioning if necessary
        subtitle = subtitle.with_position(("center", y_position - subtitle.size[1] // 2))  # Center vertically
        subtitle = subtitle.with_duration(duration_per_line).with_start(start_time)
        
        subtitle_clips.append(subtitle)
    
    print("Subtitles created!")
    return subtitle_clips


# Step 4: Assemble the Video
def create_video_with_voiceover(script_text, background_video_file, output_video_file):
    # Generate the voiceover
    audio_file = "voiceover.mp3"
    generate_voiceover(script_text, audio_file)
    #generate_google_cloud_voiceover(script_text, audio_file)

    
    # Load the background video
    video = VideoFileClip(background_video_file)
    video_duration = video.duration
    
    # Load the voiceover audio
    audio = AudioFileClip(audio_file)
    audio_duration = audio.duration

    # Adjust video duration to match audio duration
    if video_duration < audio_duration:
        # If video is shorter than audio, extend the video by repeating the last frame or adding black frames
        video = video.fx(vfx.loop, duration=audio_duration)
    else:
        # If video is longer than audio, trim the video to match audio duration
        video = video.subclipped(0, audio_duration)
    
    video_size = video.size
    
    # Resize to vertical format (e.g., 1080x1920 for portrait)
    vertical_size = (1080, 1920)  # Define your desired vertical resolution
    video = video.resized(vertical_size)
    
    # Create subtitles
    subtitles = create_subtitle_clips_dynamically(script_text, audio_file, vertical_size)
    
    # Add the voiceover to the video
    video = video.with_audio(audio)
    
    # Combine video and subtitles
    final_video = CompositeVideoClip([video, *subtitles])
    
    # Write the final video
    print("Rendering final video...")
    final_video.write_videofile(output_video_file, codec="libx264", audio_codec="aac")
    
    # Clean up temporary audio file
    os.remove(audio_file)
    print("Video creation complete!")
    
    
def generateScriptGPT():
    
    openai.api_type = "azure"
    openai.api_base = "https://chatj.openai.azure.com/"  # Replace with your endpoint
    openai.api_version = "2023-05-15"  
    openai.api_key = AZURE_CHAT_KEY # Replace with your API key

    deployment_name = "your-deployment-name"  # Replace with your deployment name

    # List of different prompt starters
    prompt_starters = [
        "Did you know that...",
        "What if I told you...",
        "Here’s something fascinating:",
        "Imagine this:",
        "The universe is full of mysteries, like...",
        "Let’s talk about something extraordinary:",
        "Here’s a mind-blowing fact:",
        "Have you ever considered that...",
        "The cosmos hides secrets like...",
        "Let me amaze you with this:"
    ]

    starter = random.choice(prompt_starters)

    # Construct the full prompt
    prompt = f"{starter} The vastness of space and its wonders."

    # Send request to Azure OpenAI
    response = openai.completions.create(
            model="gpt-4",  # or use another model of your choice
            prompt="Write a captivating, under-one-minute script about space.",
            max_tokens=150,
            temperature=0.7
        )
    script = response['choices'][0]['text'].strip()
    print(script)
    return script

    # Extract and return the response
    print(response['choices'][0]['message']['content'])
    return response['choices'][0]['message']['content']


        
    
def generateScript():
    #generateScriptGPT()
    global topic
    
    subjects=["mars","venus","mercury","saturn","jupiter","neptune","uranus","pluto","blackholes","exoplanets","sun","space mission by nasa","space mission by soviet union"]
    # subjects = [
    # "mars", "venus", "mercury", "saturn", "jupiter", "neptune", "uranus", 
    # "pluto", "blackholes", "exoplanets", "sun", "space mission by nasa", 
    # "space mission by soviet union", "asteroids", "comets", "moon", 
    # "galaxies", "the milky way", "solar eclipse", "lunar eclipse", 
    # "astronauts", "dark matter", "cosmic rays", "nebulae", "supernova", 
    # "space exploration history", "space telescopes", "gravitational waves"]
    
    subject = random.choice(subjects)
    topic=subject
    
    


    genai.configure(api_key="AIzaSyBOfFSYxtJZlG66m370mPR-3kJ7Sf3vkDQ")
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(f'''Write a captivating, under-one-minute (under 114 words) script about a space topic preferably an intresting fact about {subject}
                                      Begin with a thought-provoking question to grab attention, followed by an engaging description of the subject.  
                                      Use clear and simple language, with vivid imagery, and aim for a narrative that can be easily understood and appreciated by a broad audience.''')


    #response=model.generate_content("Intersting video script text for why saturn has rings must be under 45 seconds")

    print(response.text)
    return response.text

# Main script
if __name__ == "__main__":
    # Script text
    
    topic=""
    script = generateScript()
    
    
    # URL of a copyright-free space video (replace with a valid URL)
    background_video = "space_video1.mp4"
    output_video = "space_exploration_video.mp4"
    
    # Download the video
    #download_space_video(video_url, background_video)
    
    
    createBGVideo(background_video)
    
    # Create the video
    create_video_with_voiceover(script, background_video, output_video)
