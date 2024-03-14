from flask import Flask, request, jsonify
from pymongo import MongoClient
import language_tool_python
import nltk
from nltk.tokenize import sent_tokenize

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['certificates_db']
collection = db['certificates']

# Function to correct grammar using LanguageTool
def grammarCorrector(text):
    tool = language_tool_python.LanguageTool('en-US')
    result = tool.correct(text)
    return result

# Function to perform text summarization using NLTK
def textSummarizer(text):
    sentences = sent_tokenize(text)
    summary = ' '.join(sentences[:2])  # Summarize the text to the first two sentences
    return summary

# Function to store record in MongoDB
def store_record_in_mongodb(record):
    return collection.insert_one(record).inserted_id

# Function to determine category based on OCR text
def determine_category(ocr_text):
    # List of keywords associated with medical records
    medical_keywords = ['medical', 'health', 'doctor', 'hospital', 'clinic', 'treatment']

    # Check if any medical keyword is present in the OCR text
    for keyword in medical_keywords:
        if keyword in ocr_text.lower():
            return 'medical'

    # If no medical keyword is found, assume non-medical
    return 'non_medical'

# Endpoint to receive OCR text and trigger record generation
@app.route('/generate_record', methods=['POST'])
def generate_record_endpoint():
    data = request.get_json()
    ocr_text = data.get('ocr_text')
    email = data.get('email')

    # Determine category based on OCR text
    category = determine_category(ocr_text)

    if category == 'medical':
        # Correct grammar in OCR text
        corrected_text = grammarCorrector(ocr_text)
        
        # Summarize corrected text using NLTK
        summarized_text = textSummarizer(corrected_text)

        medical_record_info = {
            'type': 'medical',
            'reason': summarized_text,
            'email': email
        }
        record_id = store_record_in_mongodb(medical_record_info)
    else:
        # For non-medical category, extract subject and body summary from OCR text
        lines = ocr_text.split('\n')
        subject = lines[0].strip()
        body_summary = textSummarizer(' '.join(lines[1:]))  # Summarize the body summary using NLTK
        non_medical_info = {
            'type': 'non_medical',
            'reason': subject + " " + body_summary,
            'email': email
        }
        record_id = store_record_in_mongodb(non_medical_info)

    # Convert ObjectId to string for JSON serialization
    record_info = collection.find_one({'_id': record_id})
    record_info['_id'] = str(record_info['_id'])

    return jsonify({'record_type': category, 'record_data': record_info})

if __name__ == '__main__':
    nltk.download('punkt')  # Download NLTK tokenizer models
    app.run(debug=True)
