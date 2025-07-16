import re
import string
import logging
import traceback
from collections import Counter
from flask import Flask, request, jsonify
import pandas as pd
import joblib
import nltk
from textblob import TextBlob
from marshmallow import Schema, fields, ValidationError
import pdfplumber
from docx import Document

# Ensure NLTK stopwords are available
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

from nltk.corpus import stopwords

# Initialize Flask app
app = Flask(__name__)

# Load model
MODEL = joblib.load('model.pkl')

# Configuration
REQUIRED_FEATURES = ['feature1', 'feature2',
                     'feature3', 'feature4', 'feature5']
STOP_WORDS = set(stopwords.words('english'))
logging.basicConfig(level=logging.INFO)


# ========== Marshmallow Validation ==========
class FileSchema(Schema):
    file = fields.Raw(required=True)


# ========== Structured Data Utilities ==========
def read_uploaded_file(file):
    filename = file.filename.lower()
    try:
        if filename.endswith('.csv'):
            try:
                df = pd.read_csv(file)
            except UnicodeDecodeError:
                file.seek(0)
                df = pd.read_csv(file, encoding='latin1')
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        elif filename.endswith('.json'):
            df = pd.read_json(file)
        elif filename.endswith('.parquet'):
            df = pd.read_parquet(file)
        else:
            return None, "Unsupported file type. Use CSV, Excel, JSON, or Parquet."
        return df, None
    except Exception as e:
        return None, f"Failed to read file: {str(e)}"


def validate_and_prepare(df):
    missing = [col for col in REQUIRED_FEATURES if col not in df.columns]
    if missing:
        return None, f"Missing required columns: {', '.join(missing)}"
    df = df[REQUIRED_FEATURES].fillna(df.mean(numeric_only=True))
    return df, None


def generate_prescriptions(predictions):
    return ["High risk: Intensive treatment recommended." if pred == 1 else "Low risk: Standard monitoring." for pred in predictions]


def compute_financial_metrics(df):
    total_revenue = df['paid_amount'].sum()
    total_outstanding = (df['total_charge'] - df['paid_amount']).sum()
    avg_revenue_per_patient = df['paid_amount'].mean()
    revenue_by_dept = df.groupby('department')['paid_amount'].sum().to_dict()
    return {
        "total_revenue": round(total_revenue, 2),
        "total_outstanding": round(total_outstanding, 2),
        "avg_revenue_per_patient": round(avg_revenue_per_patient, 2),
        "revenue_by_department": revenue_by_dept
    }


def compute_hospital_metrics(df):
    df['admission_date'] = pd.to_datetime(
        df['admission_date'], errors='coerce')
    df['discharge_date'] = pd.to_datetime(
        df['discharge_date'], errors='coerce')
    df['stay_length'] = (df['discharge_date'] - df['admission_date']).dt.days
    avg_stay = df['stay_length'].mean()
    ward_distribution = df['ward'].value_counts().to_dict()
    admission_trends = df['admission_date'].dt.to_period(
        "M").value_counts().sort_index().to_dict()
    return {
        "average_stay_length_days": round(avg_stay, 2),
        "ward_distribution": ward_distribution,
        "monthly_admissions": {str(k): v for k, v in admission_trends.items()}
    }


# ========== Unstructured Text Utilities ==========
def clean_and_tokenize(text):
    words = re.findall(r'\b\w+\b', text.lower())
    return [w for w in words if w not in STOP_WORDS and not w.isdigit() and w not in string.punctuation]


def analyze_unstructured_text(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    sentiment = "positive" if polarity > 0.1 else "negative" if polarity < -0.1 else "neutral"
    tokens = clean_and_tokenize(text)
    top_keywords = Counter(tokens).most_common(10)
    return {
        "polarity_score": round(polarity, 3),
        "sentiment_class": sentiment,
        "top_keywords": top_keywords,
        "word_count": len(tokens)
    }


def extract_text_from_file(file):
    filename = file.filename.lower()
    text = ""
    try:
        if filename.endswith('.txt'):
            text = file.read().decode('utf-8')
        elif filename.endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                text = "\n".join(page.extract_text()
                                 or '' for page in pdf.pages)
        elif filename.endswith('.docx'):
            doc = Document(file)
            text = "\n".join(para.text for para in doc.paragraphs)
        else:
            return None, "Unsupported file type. Use .txt, .pdf, or .docx."

        if not text.strip():
            return None, "File is empty or unreadable."

        return text, None
    except Exception as e:
        return None, f"Failed to extract text: {str(e)}"


# ========== Routes ==========
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = FileSchema().load(request.files)
        file = data['file']
        df, error = read_uploaded_file(file)
        if error:
            return jsonify({'error': error}), 400
        if df.empty:
            return jsonify({'error': 'Uploaded file is empty.'}), 400

        df_validated, error = validate_and_prepare(df)
        if error:
            return jsonify({'error': error}), 400

        probabilities = MODEL.predict_proba(df_validated)[:, 1].tolist(
        ) if hasattr(MODEL, 'predict_proba') else None
        predictions = MODEL.predict(df_validated).tolist()
        prescriptions = generate_prescriptions(predictions)

        return jsonify({
            'input_rows': len(df_validated),
            'predictions': predictions,
            'probabilities': probabilities,
            'prescriptions': prescriptions
        })
    except Exception as e:
        logging.error("/predict error: %s", traceback.format_exc())
        return jsonify({'error': 'Internal Server Error'}), 500


@app.route('/analyze_text', methods=['POST'])
def analyze_text():
    try:
        data = FileSchema().load(request.files)
        file = data['file']
        text, error = extract_text_from_file(file)
        if error:
            return jsonify({'error': error}), 400

        result = analyze_unstructured_text(text)
        return jsonify(result)
    except Exception as e:
        logging.error("/analyze_text error: %s", traceback.format_exc())
        return jsonify({'error': 'Internal Server Error'}), 500


@app.route('/analyze_metrics', methods=['POST'])
def analyze_metrics():
    try:
        data = FileSchema().load(request.files)
        file = data['file']
        df, error = read_uploaded_file(file)
        if error:
            return jsonify({'error': error}), 400
        if df.empty:
            return jsonify({'error': 'Uploaded file is empty.'}), 400

        financial = compute_financial_metrics(df)
        hospital = compute_hospital_metrics(df)

        return jsonify({
            'financial_metrics': financial,
            'hospital_metrics': hospital
        })
    except Exception as e:
        logging.error("/analyze_metrics error: %s", traceback.format_exc())
        return jsonify({'error': 'Internal Server Error'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
