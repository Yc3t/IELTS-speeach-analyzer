# IELTS Speech Analyzer

IELTS Speech Analyzer is a web application that helps users improve their IELTS speaking skills by analyzing audio recordings and providing detailed feedback.

## Features

- Upload MP4 video files for analysis
- Convert video to audio for processing
- Transcribe speech using Whisper AI model
- Analyze speech based on IELTS Speaking Band Descriptors
- Provide detailed feedback on Fluency and Coherence, Lexical Resource, and Grammatical Range and Accuracy
- Generate an estimated IELTS band score
- Offer specific suggestions for improvement
- Store and manage recent analyses

## Prerequisites

- Python 3.7+
- Flask
- MoviePy
- Groq API access
- Whisper AI model

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/Yc3t/IELTS-speech-analyzer
   cd ielts-speech-analyzer
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add your Groq API key:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```
5. create a `data` folder in the directory

## Usage

1. Start the Flask server:
   ```
   python app.py
   ```

2. Open a web browser and navigate to `http://localhost:5000`

3. Use the interface to upload an MP4 file of your IELTS speaking practice

4. Wait for the analysis to complete

5. Review the detailed feedback and suggestions for improvement

## Project Structure

- `app.py`: Main Flask application
- `static/`: Contains CSS, JavaScript, and image files
- `templates/`: Contains HTML templates
- `data/`: Stores uploaded audio files and analysis results
- `requirements.txt`: List of Python dependencies

## Extra
- `S2T.py`: aislated speech to text functionality
