import os
import json
import tempfile
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from moviepy.editor import AudioFileClip
from groq import Groq
from dotenv import load_dotenv
import markdown
from datetime import datetime
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'data', 'audio')
app.config['ANALYSIS_FOLDER'] = os.path.join(os.path.dirname(__file__), 'data', 'analysis')
app.config['ENTRIES_FILE'] = os.path.join(os.path.dirname(__file__), 'data', 'entries.json')

# Create necessary folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['ANALYSIS_FOLDER'], exist_ok=True)

# Initialize Groq client with API key from .env
groq_api_key = os.getenv('GROQ_API_KEY')
if not groq_api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")
client = Groq(api_key=groq_api_key)

def get_entries():
    if os.path.exists(app.config['ENTRIES_FILE']):
        with open(app.config['ENTRIES_FILE'], 'r') as f:
            return json.load(f)
    return []

def save_entries(entries):
    with open(app.config['ENTRIES_FILE'], 'w') as f:
        json.dump(entries, f)

def convert_to_mp3(file):
    # Create a temporary file to save the uploaded content
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    file.save(temp_file.name)
    temp_file.close()

    # Generate output filename
    mp3_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
    mp3_path = os.path.join(app.config['UPLOAD_FOLDER'], mp3_filename)

    try:
        # Convert to MP3
        audio = AudioFileClip(temp_file.name)
        audio.write_audiofile(mp3_path, verbose=False, logger=None)
        audio.close()
    finally:
        # Clean up the temporary file
        os.unlink(temp_file.name)

    return mp3_path, mp3_filename
def transcribe_audio(mp3_path):
    with open(mp3_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(mp3_path, file.read()),
            model="whisper-large-v3",
            prompt="",
            response_format="json",
            temperature=0,
        )
    return transcription.text

def analyze_speech(transcription):
    prompt = f"""
    You are an expert IELTS examiner. Analyze the following transcribed speech based on the IELTS Speaking Band Descriptors. Provide detailed feedback and suggestions for improvement in each category. Use the transcription to support your analysis with specific examples.

    Transcription:
    {transcription}

    Provide your analysis in the following format:
    # Feedback
    ## Fluency and Coherence
    [Detailed analysis with specific examples from the transcript. Include suggestions for improvement, such as specific phrases or techniques to enhance fluency and coherence.]

    ## Lexical Resource
    [Detailed analysis with specific examples from the transcript. Highlight strong vocabulary choices and areas for improvement. Suggest specific words or phrases that could elevate the speaker's language use.]

    ## Grammatical Range and Accuracy
    [Detailed analysis with specific examples from the transcript. Point out both correct and incorrect grammar usage. Provide specific corrections for grammatical errors and suggest more complex structures where appropriate.]

    ## Overall Band Score
    [Provide an estimated overall band score based on the analysis, with a brief explanation of why this score was given.]

    ## Detailed Suggestions for Improvement
    1. Fluency and Coherence:
       - [List 3-5 specific strategies or exercises to improve fluency and coherence]
    2. Lexical Resource:
       - [List 5-7 specific words or phrases the speaker could incorporate to enhance their vocabulary]
       - [Suggest 2-3 topics the speaker could study to broaden their lexical range]
    3. Grammatical Range and Accuracy:
       - [List 3-5 specific grammar points the speaker should focus on, with examples of correct usage]
       - [Suggest 2-3 complex grammatical structures the speaker could incorporate, with examples]

    Remember to be constructive in your feedback, highlighting the areas for improvement.
    """

    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.5,
        max_tokens=5160,
        top_p=1,
        stream=False,
        stop=None,
    )
    
    return completion.choices[0].message.content

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and file.filename.lower().endswith('.mp4'):
        try:
            mp3_path, mp3_filename = convert_to_mp3(file)
            transcription = transcribe_audio(mp3_path)
            analysis = analyze_speech(transcription)
            
            # Combine transcript and analysis
            full_content = f"# Transcript\n\n{transcription}\n\n{analysis}"
            
            # Save full content to HTML file
            html_content = markdown.markdown(full_content)
            analysis_html_filename = f"{os.path.splitext(mp3_filename)[0]}_analysis.html"
            analysis_html_path = os.path.join(app.config['ANALYSIS_FOLDER'], analysis_html_filename)
            with open(analysis_html_path, 'w') as f:
                f.write(html_content)
            
            # Save full content to TXT file
            analysis_txt_filename = f"{os.path.splitext(mp3_filename)[0]}_analysis.txt"
            analysis_txt_path = os.path.join(app.config['ANALYSIS_FOLDER'], analysis_txt_filename)
            with open(analysis_txt_path, 'w') as f:
                f.write(full_content)
            
            # Create entry for recent analyses
            entry = {
                'filename': mp3_filename,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'analysis_html': analysis_html_filename,
                'analysis_txt': analysis_txt_filename
            }
            
            # Update entries
            entries = get_entries()
            entries.insert(0, entry)
            entries = entries[:5]  # Keep only the 5 most recent entries
            save_entries(entries)
            
            return jsonify({'analysis': html_content, 'entry': entry})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/analysis/<filename>')
def get_analysis(filename):
    return send_from_directory(app.config['ANALYSIS_FOLDER'], filename)

@app.route('/recent_entries')
def recent_entries():
    entries = get_entries()
    return jsonify(entries)
@app.route('/delete_entry/<filename>', methods=['DELETE'])
def delete_entry(filename):
    entries = get_entries()
    for entry in entries:
        if entry['filename'] == filename:
            # Delete associated files
            mp3_path = os.path.join(app.config['UPLOAD_FOLDER'], entry['filename'])
            html_path = os.path.join(app.config['ANALYSIS_FOLDER'], entry['analysis_html'])
            txt_path = os.path.join(app.config['ANALYSIS_FOLDER'], entry['analysis_txt'])
            
            try:
                if os.path.exists(mp3_path):
                    os.remove(mp3_path)
                if os.path.exists(html_path):
                    os.remove(html_path)
                if os.path.exists(txt_path):
                    os.remove(txt_path)
                
                # Remove entry from list
                entries.remove(entry)
                save_entries(entries)
                return jsonify({'success': True, 'message': 'Entry deleted successfully'})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500
    
    return jsonify({'success': False, 'message': 'Entry not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)