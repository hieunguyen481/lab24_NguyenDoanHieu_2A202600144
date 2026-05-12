"""Shared configuration for Lab 18."""

import os
from dotenv import load_dotenv

load_dotenv()

# --- API Keys ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")

# --- Qdrant ---
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "lab18_production"
NAIVE_COLLECTION = "lab18_naive"

# --- Embedding ---
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024

# --- Chunking ---
HIERARCHICAL_PARENT_SIZE = 2048
HIERARCHICAL_CHILD_SIZE = 256
SEMANTIC_THRESHOLD = 0.85

# --- Search ---
BM25_TOP_K = 20
DENSE_TOP_K = 20
HYBRID_TOP_K = 20
RERANK_TOP_K = 7

# --- Paths ---
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
TEST_SET_PATH = os.path.join(os.path.dirname(__file__), "test_set.json")
ADVERSARIAL_TEST_SET_PATH = os.path.join(os.path.dirname(__file__), "adversarial_test_set.json")
HUMAN_ANNOTATIONS_PATH = os.path.join(os.path.dirname(__file__), "human_annotations.json")

# --- Lab 24: Guardrails ---
ALLOWED_TOPICS = [
    "pháp luật", "thuế", "dữ liệu cá nhân", "tài chính",
    "bảo vệ dữ liệu", "nghị định", "quy định", "doanh nghiệp",
    "kế toán", "báo cáo tài chính", "GTGT", "VAT",
]
PII_PATTERNS_VN = {
    "CCCD": r"\b\d{12}\b",
    "PHONE_VN": r"\b(0[3|5|7|8|9])\d{8}\b",
    "MST": r"\b\d{10}(-\d{3})?\b",
}

# --- Lab 24: LLM-Judge ---
JUDGE_MODEL = "gpt-4o-mini"
JUDGE_CRITERIA = ["correctness", "completeness", "relevance", "coherence"]

# --- Lab 24: SLO Thresholds ---
SLO = {
    "faithfulness": 0.90,
    "answer_relevancy": 0.85,
    "context_precision": 0.80,
    "context_recall": 0.90,
    "p95_latency_s": 3.0,
    "pii_leak_rate": 0.0,
}
