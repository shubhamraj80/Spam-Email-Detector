"""
train_model.py - Machine Learning Model Training
=================================================
This script:
1. Loads the labeled email dataset (spam/ham)
2. Preprocesses the text
3. Extracts features using TF-IDF
4. Trains a Logistic Regression classifier
5. Evaluates with accuracy, classification report, confusion matrix
6. Saves the model and vectorizer using pickle
"""

import os
import sys
import pickle
import logging
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np

# Add parent directory to path so we can import preprocessing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preprocessing import preprocess_text

# ─── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_PATH   = os.path.join(BASE_DIR, 'data', 'emails.csv')
MODEL_DIR   = os.path.join(BASE_DIR, 'model')
MODEL_PATH  = os.path.join(MODEL_DIR, 'spam_model.pkl')
TFIDF_PATH  = os.path.join(MODEL_DIR, 'tfidf_vectorizer.pkl')

os.makedirs(MODEL_DIR, exist_ok=True)


# ─── 1. Load Dataset ──────────────────────────────────────────────────────────
def load_data(path: str) -> pd.DataFrame:
    logger.info(f"Loading dataset from: {path}")
    df = pd.read_csv(path)
    logger.info(f"Dataset shape: {df.shape}")
    logger.info(f"Label distribution:\n{df['label'].value_counts()}")
    return df


# ─── 2. Preprocess ────────────────────────────────────────────────────────────
def prepare_features(df: pd.DataFrame):
    logger.info("Preprocessing text data...")
    df['clean_text'] = df['text'].apply(preprocess_text)

    # Encode labels: spam=1, ham=0
    df['label_encoded'] = df['label'].map({'spam': 1, 'ham': 0})

    X = df['clean_text']
    y = df['label_encoded']

    logger.info(f"Sample preprocessed text: {X.iloc[0][:80]}...")
    return X, y


# ─── 3. TF-IDF Vectorization ─────────────────────────────────────────────────
def build_vectorizer(X_train):
    """
    TF-IDF (Term Frequency–Inverse Document Frequency):
    - Converts raw text into numerical feature vectors.
    - Words frequent in a document but rare across all docs get high weight.
    - max_features=5000: keep top 5000 most informative words.
    - ngram_range=(1,2): use both single words and pairs (bigrams).
    """
    logger.info("Building TF-IDF vectorizer...")
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        sublinear_tf=True       # Apply log normalization to TF
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    logger.info(f"Feature matrix shape: {X_train_vec.shape}")
    return vectorizer, X_train_vec


# ─── 4. Train Model ───────────────────────────────────────────────────────────
def train_model(X_train_vec, y_train):
    """
    Logistic Regression:
    - Works well for text classification tasks.
    - Learns weights for each TF-IDF feature (word).
    - max_iter=1000 ensures convergence.
    - C=1.0 is regularization strength (prevents overfitting).
    """
    logger.info("Training Logistic Regression model...")
    model = LogisticRegression(
        C=1.0,
        max_iter=1000,
        solver='lbfgs',
        random_state=42
    )
    model.fit(X_train_vec, y_train)
    logger.info("Model training complete!")
    return model


# ─── 5. Evaluate ──────────────────────────────────────────────────────────────
def evaluate_model(model, vectorizer, X_test, y_test):
    X_test_vec = vectorizer.transform(X_test)
    y_pred     = model.predict(X_test_vec)

    accuracy = accuracy_score(y_test, y_pred)
    cm       = confusion_matrix(y_test, y_pred)

    # ── Console output (unchanged) ──────────────────────────────────────
    logger.info(f"\n{'='*50}")
    logger.info("MODEL EVALUATION RESULTS")
    logger.info(f"{'='*50}")
    logger.info(f"Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    logger.info(f"\nClassification Report:\n{classification_report(y_test, y_pred, target_names=['Ham','Spam'])}")
    logger.info(f"Confusion Matrix:\n{cm}")
    logger.info(f"{'='*50}")

    # ── Visual output ────────────────────────────────────────────────────
    _plot_results(accuracy, cm)

    return accuracy


def _plot_results(accuracy: float, cm: np.ndarray):
    """Render accuracy gauge + confusion matrix and save to model dir."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.suptitle("Spam Classifier — Evaluation", fontsize=14, fontweight="bold", y=1.02)

    # ── Panel 1: Accuracy gauge (donut chart) ────────────────────────────
    ax1 = axes[0]
    wrong = 1.0 - accuracy
    wedge_colors = ["#4F8EF7", "#E8EDF5"]
    wedges, _ = ax1.pie(
        [accuracy, wrong],
        colors=wedge_colors,
        startangle=90,
        wedgeprops=dict(width=0.38, edgecolor="white", linewidth=2),
        counterclock=False,
    )
    ax1.text(0, 0.08, f"{accuracy*100:.1f}%",
             ha="center", va="center", fontsize=26, fontweight="bold", color="#1A1A2E")
    ax1.text(0, -0.22, "Accuracy",
             ha="center", va="center", fontsize=11, color="#666")
    correct   = int(cm[0,0] + cm[1,1])
    incorrect = int(cm[0,1] + cm[1,0])
    legend_items = [
        mpatches.Patch(color="#4F8EF7", label=f"Correct ({correct})"),
        mpatches.Patch(color="#E8EDF5", label=f"Wrong ({incorrect})"),
    ]
    ax1.legend(handles=legend_items, loc="lower center",
               bbox_to_anchor=(0.5, -0.12), ncol=2, fontsize=9, frameon=False)
    ax1.set_title("Overall accuracy", fontsize=11, pad=12)

    # ── Panel 2: Confusion matrix heatmap ────────────────────────────────
    ax2    = axes[1]
    labels = ["Ham", "Spam"]
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=labels, yticklabels=labels,
        linewidths=0.5, linecolor="white",
        annot_kws={"size": 18, "weight": "bold"},
        ax=ax2,
    )
    ax2.set_xlabel("Predicted label", fontsize=10, labelpad=8)
    ax2.set_ylabel("Actual label",    fontsize=10, labelpad=8)
    ax2.set_title("Confusion matrix",  fontsize=11, pad=12)
    ax2.tick_params(axis="both", which="both", length=0)

    # ── Save ─────────────────────────────────────────────────────────────
    out_path = os.path.join(MODEL_DIR, "evaluation.png")
    plt.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Evaluation plot saved → {out_path}")

# ─── 6. Save Model ────────────────────────────────────────────────────────────
def save_artifacts(model, vectorizer):
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to: {MODEL_PATH}")

    with open(TFIDF_PATH, 'wb') as f:
        pickle.dump(vectorizer, f)
    logger.info(f"Vectorizer saved to: {TFIDF_PATH}")


# ─── Main Pipeline ────────────────────────────────────────────────────────────
def main():
    logger.info("Starting spam classifier training pipeline...")

    # Load
    df = load_data(DATA_PATH)

    # Preprocess
    X, y = prepare_features(df)

    # Train/Test split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

    # Vectorize
    vectorizer, X_train_vec = build_vectorizer(X_train)

    # Train
    model = train_model(X_train_vec, y_train)

    # Evaluate
    evaluate_model(model, vectorizer, X_test, y_test)

    # Save
    save_artifacts(model, vectorizer)

    logger.info("\n✅ Training pipeline complete! Model is ready for deployment.")


if __name__ == "__main__":
    main()
