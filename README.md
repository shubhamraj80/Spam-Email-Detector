# 📧 Email Spam Detector

A complete machine learning web application that classifies emails as **Spam** or **Ham (Legitimate)** using TF-IDF feature extraction and Logistic Regression.

---

## 🗂 Project Structure

```
spam_detector/
├── data/
│   ├── emails.csv              ← Labeled dataset (spam/ham)
│   └── generate_dataset.py     ← Script to regenerate the dataset
│
├── model/
│   ├── spam_model.pkl          ← Trained Logistic Regression model
│   └── tfidf_vectorizer.pkl    ← Fitted TF-IDF vectorizer
│
├── templates/
│   └── index.html              ← Frontend HTML (Jinja2 template)
│
├── static/
│   ├── css/style.css           ← Styles
│   └── js/app.js               ← Frontend JS (API calls)
│
├── preprocessing.py            ← Text cleaning module
├── train_model.py              ← ML training pipeline
├── app.py                      ← Flask backend (API)
├── requirements.txt
└── README.md
```
---

## System Diagram

![system diagram](/sys_diagram.png)


---

## ⚡ How to Run Locally

### 1. Clone / Download the project
```bash
git clone  https://github.com/imSHR3YA/spam-detector
cd spam-detector
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Train the model
```bash
python train_model.py
```
This generates `model/spam_model.pkl` and `model/tfidf_vectorizer.pkl`.

### 5. Run the Flask server
```bash
python app.py
```

### 6. Open in browser
```
http://localhost:5000
```

---

## 🔌 API Endpoints

| Method | Endpoint   | Description                        |
|--------|------------|------------------------------------|
| GET    | `/health`  | Check server and model status      |
| POST   | `/predict` | Classify email text as spam or ham |

### POST /predict — Example

**Request:**
```json
{
  "email": "Congratulations! You've won $1,000,000. Click here to claim!"
}
```

**Response:**
```json
{
  "prediction": "spam",
  "confidence": 0.9987,
  "confidence_pct": "99.9%",
  "is_spam": true,
  "message": "⚠️ This email appears to be SPAM.",
  "processed_text_preview": "congratulations won click claim"
}
```

---

## How the Model Works  

### Step 1 — Text Preprocessing (`preprocessing.py`)
Raw email text goes through a cleaning pipeline:
1. **Lowercase**: `"CLICK HERE"` → `"click here"`
2. **Remove URLs**: strips `http://...` links
3. **Remove punctuation**: strips `!`, `$`, `.`, etc.
4. **Remove digits**: strips `1000000`, `24`, etc.
5. **Remove stopwords**: common words like `"the"`, `"is"`, `"you"` are removed
6. **Result**: only meaningful, informative words remain

**Why?** These steps reduce noise and help the model focus on words that actually signal spam vs ham.

### Step 2 — TF-IDF Vectorization (`TfidfVectorizer`)
- Converts cleaned text into a numerical matrix
- **TF (Term Frequency)**: How often a word appears in THIS email
- **IDF (Inverse Document Frequency)**: How rare the word is ACROSS all emails
- Words rare everywhere (IDF boost) but frequent in THIS email → high score
- `max_features=5000` keeps the top 5000 most useful words
- `ngram_range=(1,2)` captures both single words and 2-word phrases

**Example**: "free prize" as a bigram is stronger than just "free" and "prize" separately.

### Step 3 — Logistic Regression (`LogisticRegression`)
- Takes the TF-IDF feature vector as input
- Learns a weight for each word: spam words get high positive weights, ham words get negative weights
- Outputs a probability (0 to 1): `> 0.5 → spam`
- `predict_proba()` gives the confidence score

### Step 4 — Model Persistence (`pickle`)
- `pickle.dump()` serializes the trained model and vectorizer to `.pkl` files
- `pickle.load()` reloads them at Flask startup — no retraining needed

---

## 🌐 How the Backend Works (`app.py`)

Flask is a lightweight Python web framework.

```
Request: POST /predict
   ↓
Input validation (empty text? too short?)
   ↓
preprocess_text(email) → clean_text
   ↓
vectorizer.transform([clean_text]) → feature_vector
   ↓
model.predict(feature_vector) → 0 (ham) or 1 (spam)
model.predict_proba() → confidence score
   ↓
Return JSON response
```

Key Flask concepts used:
- `@app.route('/predict', methods=['POST'])` — defines the endpoint
- `request.get_json()` — reads the JSON body
- `jsonify(...)` — returns a JSON response

---

## 🎨 How the Frontend Connects (`app.js`)

JavaScript `fetch()` API sends a POST request to Flask:

```javascript
const response = await fetch('/predict', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: emailText })
});
const data = await response.json();
// Update UI with data.prediction, data.confidence, etc.
```

**Data flow:**
```
User types email
    → JS validates input
    → fetch('/predict', { email: text })
    → Flask preprocesses → model predicts
    → JSON response returned
    → JS renders result card with verdict + confidence bar
```

---

## 📤 Push to GitHub

```bash
# Initialize git repo
git init
git add .
git commit -m "Initial commit: Email Spam Detector"

# Create repo on GitHub, then:
git remote add origin  https://github.com/imSHR3YA/spam-detector
git branch -M main
git push -u origin main
```

**Add a `.gitignore`:**
```
venv/
__pycache__/
*.pyc
model/*.pkl
.env
```

---

## 📊 Model Performance

| Metric    | Score  |
|-----------|--------|
| Accuracy  | ~100%  |
| Precision | ~100%  |
| Recall    | ~100%  |

> Note: On a small curated dataset, accuracy is very high. On real-world email data (e.g., Enron dataset, SpamAssassin), expect 95-99% accuracy.

---

## 🔬 Possible Improvements

- Use **Enron email dataset** (500k+ real emails) for better generalization
- Try **Naive Bayes** (`MultinomialNB`) — often faster and competitive for text
- Add **LIME** explainability to show which words triggered the spam verdict
- Deploy to **Heroku / Render / Railway** for public access
- Add rate limiting and API key authentication for production

---

 
