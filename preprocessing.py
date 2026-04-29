"""
preprocessing.py - Text Preprocessing Module
=============================================
Handles all text cleaning operations:
- Lowercasing
- Removing punctuation & special characters
- Removing stopwords (using a built-in list to avoid NLTK download issues)
- Stripping extra whitespace
"""

import re
import string

# Built-in English stopwords (subset) — avoids NLTK corpus download issues
STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're",
    "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he',
    'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's",
    'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
    'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are',
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do',
    'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because',
    'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
    'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
    'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
    'all', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
    'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't',
    'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll',
    'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't",
    'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't",
    'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn',
    "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't",
    'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"
}


def preprocess_text(text: str) -> str:
    """
    Full preprocessing pipeline for an email text.

    Steps:
    1. Lowercase the text
    2. Remove URLs
    3. Remove email addresses
    4. Remove punctuation and special characters
    5. Remove digits
    6. Remove stopwords
    7. Strip extra whitespace

    Args:
        text (str): Raw email text

    Returns:
        str: Cleaned, preprocessed text
    """
    if not isinstance(text, str) or not text.strip():
        return ""

    # Step 1: Lowercase
    text = text.lower()

    # Step 2: Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)

    # Step 3: Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)

    # Step 4: Remove punctuation and special characters
    text = text.translate(str.maketrans('', '', string.punctuation))

    # Step 5: Remove digits
    text = re.sub(r'\d+', '', text)

    # Step 6: Tokenize and remove stopwords
    tokens = text.split()
    tokens = [word for word in tokens if word not in STOPWORDS and len(word) > 1]

    # Step 7: Rejoin and strip
    return ' '.join(tokens).strip()


if __name__ == "__main__":
    # Quick test
    sample = "URGENT!! Click HERE now to CLAIM your FREE prize worth $1,000,000!"
    print("Original:", sample)
    print("Processed:", preprocess_text(sample))
