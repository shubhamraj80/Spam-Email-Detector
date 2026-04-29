"""
app.py - Flask Backend for Email Spam Detector
===============================================
Provides REST API endpoints:
  GET  /health   → Returns server status
  POST /predict  → Classifies email as spam or ham
  POST /predict_batch → Batch CSV analysis
 
The model and vectorizer are loaded once at startup for efficiency.
"""
 
import os
import sys
import pickle
import logging
import csv
import io
from flask import Flask, request, jsonify, render_template

# Try to import ollama for hybrid LLM fallback
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
 
# Ensure local modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preprocessing import preprocess_text
 
# ─── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)
 
# ─── Flask App ────────────────────────────────────────────────────────────────
app = Flask(__name__)
 
# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'model', 'spam_model.pkl')
TFIDF_PATH = os.path.join(BASE_DIR, 'model', 'tfidf_vectorizer.pkl')
 
# ─── Load Model at Startup ────────────────────────────────────────────────────
model      = None
vectorizer = None
 
def load_model():
    """Load the trained model and TF-IDF vectorizer from disk."""
    global model, vectorizer
    try:
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        with open(TFIDF_PATH, 'rb') as f:
            vectorizer = pickle.load(f)
        logger.info("✅ Model and vectorizer loaded successfully.")
    except FileNotFoundError as e:
        logger.error(f"❌ Model file not found: {e}")
        logger.error("Run train_model.py first to generate the model files.")
 
load_model()


# ─── Helper Functions ─────────────────────────────────────────────────────────

def get_word_scores(email_text, clean_text, prediction):
    """
    Calculate per-word spam/ham scores using TF-IDF coefficients.
    Returns dict with word scores and annotated HTML.
    """
    try:
        tokens = clean_text.split()
        text_vector = vectorizer.transform([clean_text])
        feature_names = vectorizer.get_feature_names_out()
        
        # Get feature indices that are non-zero in this sample
        nonzero_indices = text_vector.nonzero()[1]
        scores = {}
        
        if hasattr(model, 'coef_'):
            coef = model.coef_[0]
            for idx in nonzero_indices:
                if idx < len(feature_names):
                    word = feature_names[idx]
                    score = float(coef[idx])
                    scores[word] = score
        
        # Sort by absolute value and get top 10
        sorted_scores = sorted(scores.items(), key=lambda x: abs(x[1]), reverse=True)[:10]
        
        # Create annotated HTML with original email text
        annotated_html = annotate_email_html(email_text, dict(sorted_scores))
        
        return {
            "word_scores": dict(sorted_scores),
            "annotated_html": annotated_html,
            "top_words": [w for w, _ in sorted_scores]
        }
    except Exception as e:
        logger.warning(f"Could not compute word scores: {e}")
        return {
            "word_scores": {},
            "annotated_html": f"<p>{email_text}</p>",
            "top_words": []
        }


def annotate_email_html(email_text, scores):
    """
    Create HTML with words highlighted based on spam/ham scores.
    """
    import re
    
    # Normalize scores to -1..1 range for visualization
    if not scores:
        return f"<p>{email_text}</p>"
    
    max_abs = max([abs(v) for v in scores.values()]) if scores else 0.1
    
    words = re.findall(r'\b\w+\b|\W+', email_text)
    html_parts = []
    
    for word in words:
        if re.match(r'\w+', word):
            clean_word = word.lower()
            score = scores.get(clean_word, 0)
            
            if score > 0.3:
                # Strong spam signal
                html_parts.append(f'<mark class="hl-high">{word}</mark>')
            elif score > 0.1:
                # Moderate spam signal
                html_parts.append(f'<mark class="hl-medium">{word}</mark>')
            elif score < -0.1:
                # Ham signal
                html_parts.append(f'<mark class="hl-safe">{word}</mark>')
            else:
                html_parts.append(word)
        else:
            # Whitespace/punctuation
            html_parts.append(word)
    
    return ''.join(html_parts)


def get_ollama_prediction(email_text, clean_text):
    """
    Call Ollama LLaMA for hybrid LLM analysis.
    Returns dict with prediction, confidence, reasoning.
    """
    if not OLLAMA_AVAILABLE:
        return None
    
    try:
        prompt = f"""You are an email spam detection expert.
Analyze this email and classify it as spam or ham.

Email:
{email_text}

Reply ONLY with valid JSON, no other text:
{{
  "prediction": "spam" or "ham",
  "confidence": 0.5 to 1.0,
  "reasoning": "one sentence"
}}"""
        
        response = ollama.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}]
        )
        
        import json
        content = response.get('message', {}).get('content', '{}')
        result = json.loads(content)
        
        return {
            "prediction": result.get("prediction", "ham"),
            "confidence": float(result.get("confidence", 0.5)),
            "reasoning": result.get("reasoning", "")
        }
    except Exception as e:
        logger.warning(f"Ollama call failed: {e}")
        return None

 
# ─── Routes ───────────────────────────────────────────────────────────────────
 
@app.route('/')
def index():
    """Serve the main frontend page."""
    return render_template('index.html')
 
 
@app.route('/health', methods=['GET'])
def health():
    """
    Health Check Endpoint
    ----------------------
    Returns server and model status.
    """
    status = {
        "status": "ok",
        "model_loaded": model is not None,
        "vectorizer_loaded": vectorizer is not None,
        "service": "Email Spam Detector API",
        "version": "2.0.0",
        "ollama_available": OLLAMA_AVAILABLE
    }
    logger.info("Health check requested.")
    return jsonify(status), 200
 
 
@app.route('/predict', methods=['POST'])
def predict():
    """
    Prediction Endpoint
    --------------------
    Accepts JSON: { "email": "<email text>" }
    Returns JSON with prediction, confidence, word scores, and annotated HTML.
    
    Hybrid logic:
    - If LR confidence >= 0.75 → return immediately (fast path)
    - If LR confidence < 0.75 → call Ollama LLaMA (slow path)
    """
 
    # ── Input validation ──────────────────────────────────────────────────────
    if not request.is_json:
        logger.warning("Request received without JSON content type.")
        return jsonify({"error": "Content-Type must be application/json"}), 400
 
    data = request.get_json()
    email_text = data.get('email', '').strip()
 
    if not email_text:
        logger.warning("Empty email text received.")
        return jsonify({"error": "Email text cannot be empty."}), 400
 
    if len(email_text) < 3:
        return jsonify({"error": "Email text is too short to classify."}), 400
 
    # ── Model not loaded guard ────────────────────────────────────────────────
    if model is None or vectorizer is None:
        logger.error("Prediction requested but model is not loaded.")
        return jsonify({"error": "Model not available. Please try again later."}), 503
 
    try:
        # ── Preprocessing ─────────────────────────────────────────────────────
        clean_text = preprocess_text(email_text)
        logger.info(f"Input: '{email_text[:60]}...' → Cleaned: '{clean_text[:60]}...'")
 
        # ── Vectorization ─────────────────────────────────────────────────────
        text_vector = vectorizer.transform([clean_text])
 
        # ── Prediction (Logistic Regression) ──────────────────────────────────
        prediction = model.predict(text_vector)[0]              # 0=ham, 1=spam
        probabilities = model.predict_proba(text_vector)[0]     # [p_ham, p_spam]
 
        label = "spam" if prediction == 1 else "ham"
        confidence = float(probabilities[prediction])
        p_spam = float(probabilities[1])
        p_ham = float(probabilities[0])
        
        logger.info(f"LR Prediction: {label.upper()} (confidence: {confidence:.2%})")
        
        # ── Word Scores & Annotated HTML ──────────────────────────────────────
        word_info = get_word_scores(email_text, clean_text, prediction)
        
        # ── Hybrid Logic: Check if we should escalate to Ollama ────────────────
        model_used = "logistic_regression"
        reasoning = None
        
        if confidence < 0.75 and OLLAMA_AVAILABLE:
            logger.info("LR confidence < 0.75, escalating to Ollama LLaMA...")
            ollama_result = get_ollama_prediction(email_text, clean_text)
            
            if ollama_result:
                model_used = "llama3.2"
                label = ollama_result["prediction"]
                confidence = ollama_result["confidence"]
                p_spam = confidence if label == "spam" else (1 - confidence)
                p_ham = (1 - confidence) if label == "spam" else confidence
                reasoning = ollama_result.get("reasoning")
                prediction = 1 if label == "spam" else 0
                logger.info(f"LLaMA Prediction: {label.upper()} (confidence: {confidence:.2%})")
 
        return jsonify({
            "prediction": label,
            "confidence": round(confidence, 4),
            "confidence_pct": f"{confidence * 100:.1f}%",
            "is_spam": bool(prediction == 1),
            "message": (
                "⚠️ This email appears to be SPAM."
                if prediction == 1 else
                "✅ This email looks legitimate (Ham)."
            ),
            "processed_text_preview": clean_text[:100],
            "word_scores": word_info["word_scores"],
            "annotated_html": word_info["annotated_html"],
            "top_words": word_info["top_words"],
            "p_spam": round(p_spam, 4),
            "p_ham": round(p_ham, 4),
            "model_used": model_used,
            "reasoning": reasoning
        }), 200
 
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred during prediction."}), 500


@app.route('/predict_batch', methods=['POST'])
def predict_batch():
    """
    Batch Prediction Endpoint
    --------------------------
    Accepts multipart CSV file upload.
    CSV must have a column named "text" or "email".
    Returns results with summary statistics.
    """
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part in request"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.lower().endswith('.csv'):
        return jsonify({"error": "File must be a CSV"}), 400
    
    if model is None or vectorizer is None:
        return jsonify({"error": "Model not available. Please try again later."}), 503
    
    try:
        # Read CSV
        stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        # Find email column
        email_column = None
        if csv_reader.fieldnames:
            if 'text' in csv_reader.fieldnames:
                email_column = 'text'
            elif 'email' in csv_reader.fieldnames:
                email_column = 'email'
            else:
                email_column = csv_reader.fieldnames[0]
        else:
            return jsonify({"error": "CSV is empty or invalid"}), 400
        
        results = []
        spam_count = 0
        ham_count = 0
        
        for row in csv_reader:
            email_text = row.get(email_column, '').strip()
            
            if not email_text or len(email_text) < 3:
                continue
            
            try:
                clean_text = preprocess_text(email_text)
                text_vector = vectorizer.transform([clean_text])
                prediction = model.predict(text_vector)[0]
                probabilities = model.predict_proba(text_vector)[0]
                
                label = "spam" if int(prediction) == 1 else "ham"
                confidence = float(probabilities[int(prediction)])
                
                is_spam = bool(int(prediction) == 1)   # ✅ FIXED HERE
                
                results.append({
                    "email_preview": str(email_text[:60]),
                    "prediction": label,
                    "confidence": round(confidence, 4),
                    "is_spam": is_spam
                })
                
                if is_spam:
                    spam_count += 1
                else:
                    ham_count += 1
                    
            except Exception as e:
                logger.warning(f"Error processing row: {e}")
                continue
        
        total = len(results)
        
        return jsonify({
            "results": results,
            "total": int(total),
            "spam_count": int(spam_count),
            "ham_count": int(ham_count),
            "spam_rate": float(round((spam_count / total * 100), 1)) if total > 0 else 0.0
        }), 200
        
    except Exception as e:
        logger.error(f"Batch prediction error: {e}", exc_info=True)
        return jsonify({"error": "Error processing CSV file"}), 500
# ─── Error Handlers ───────────────────────────────────────────────────────────
 
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found."}), 404
 
@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed."}), 405
 
@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error."}), 500
 
 
# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    logger.info("🚀 Starting Email Spam Detector API...")
    if OLLAMA_AVAILABLE:
        logger.info("✅ Ollama module available for hybrid LLM fallback")
    else:
        logger.info("⚠️  Ollama not installed - hybrid LLM fallback disabled")
    app.run(debug=True, host='0.0.0.0', port=5001)