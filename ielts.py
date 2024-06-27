import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from moviepy.editor import VideoFileClip
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DropArea(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        
        # Initialize Groq client with API key from .env
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
        self.client = Groq(api_key=groq_api_key)
        
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.label = QLabel("Drag and drop MP4 files here")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('MP4 to MP3 Converter with Transcription and IELTS Analysis')

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for file_path in files:
            if file_path.lower().endswith('.mp4'):
                mp3_path = self.convert_to_mp3(file_path)
                if mp3_path:
                    transcription = self.transcribe_audio(mp3_path)
                    if transcription:
                        self.analyze_speech(transcription, mp3_path)

    def convert_to_mp3(self, file_path):
        try:
            video = VideoFileClip(file_path)
            audio = video.audio
            mp3_path = os.path.splitext(file_path)[0] + '.mp3'
            audio.write_audiofile(mp3_path)
            audio.close()
            video.close()
            self.label.setText(f"Converted: {os.path.basename(mp3_path)}")
            return mp3_path
        except Exception as e:
            self.label.setText(f"Error in conversion: {str(e)}")
            return None

    def transcribe_audio(self, mp3_path):
        try:
            with open(mp3_path, "rb") as file:
                transcription = self.client.audio.transcriptions.create(
                    file=(mp3_path, file.read()),
                    model="whisper-large-v3",
                    prompt="",
                    response_format="json",
                    temperature=0,
                )
            self.label.setText(f"Transcription complete for: {os.path.basename(mp3_path)}")
            return transcription.text
        except Exception as e:
            self.label.setText(f"Error in transcription: {str(e)}")
            return None

    def analyze_speech(self, transcription, mp3_path):
        prompt = f"""
        You are an expert IELTS examiner. Analyze the following transcribed speech based on the IELTS Speaking Band Descriptors. Provide detailed feedback and suggestions for improvement in each category. Use the transcription to support your analysis with specific examples.

        Transcription:
        {transcription}

        Provide your analysis in the following format:
        # Transcript
        [Insert the full transcription here]

        # Feedback
        ## Fluency and Coherence
        [Detailed analysis and examples]

        ## Lexical Resource
        [Detailed analysis and examples]

        ## Grammatical Range and Accuracy
        [Detailed analysis and examples]


        ## Overall Band Score
        [Provide an estimated overall band score based on the analysis]

        ## Suggestions for Improvement
        [Provide specific suggestions for improvement in each category]
        """

        try:
            completion = self.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=5160,
                top_p=1,
                stream=False,
                stop=None,
            )
            
            analysis = completion.choices[0].message.content

            # Save transcription and analysis to a text file
            txt_path = os.path.splitext(mp3_path)[0] + '_analysis.txt'
            with open(txt_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write(analysis)
            
            self.label.setText(f"Analysis saved: {os.path.basename(txt_path)}")
        except Exception as e:
            self.label.setText(f"Error in analysis: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DropArea()
    ex.show()
    sys.exit(app.exec_())