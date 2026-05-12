# Lab 24 — Full Evaluation & Guardrail System

**AICB-P2T3 · Ngày 24 · VinUniversity**  
**Sinh viên:** Nguyễn Doãn Hiếu — 2A202600144  
**Hình thức:** Cá nhân

## Overview

Hệ thống production-ready evaluation và guardrail stack cho RAG pipeline từ Day 18. Lab bao gồm: (1) RAGAS evaluation pipeline với 50+ synthetic test questions đo 4 core metrics, (2) LLM-as-Judge pipeline với pairwise comparison, absolute scoring, swap-and-average bias mitigation và Cohen's kappa calibration, (3) Defense-in-depth guardrail stack gồm PII redaction (Presidio + Vietnamese regex), topic scope validator, adversarial testing, output safety check (Llama Guard 3/OpenAI Moderation), và latency benchmark end-to-end, (4) Blueprint document cho production deployment với SLO, architecture diagram, alert playbook, và cost analysis.

## Setup

```bash
# 1. Clone & install
git clone <repo-url> && cd lab24-eval-guardrails
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 2. API keys
cp .env.example .env    # Điền OPENAI_API_KEY (bắt buộc)

# 3. Qdrant
docker compose up -d
```

## Quick Start

```bash
# Chạy toàn bộ 4 phases
python main_lab24.py

# Hoặc từng phase riêng
python main_lab24.py --phase A   # RAGAS Evaluation
python main_lab24.py --phase B   # LLM-Judge
python main_lab24.py --phase C   # Guardrails

# Kiểm tra deliverables
python check_lab24.py
```

## Results Summary

### Phase A — RAGAS Evaluation (30 điểm)

- **Test set:** 55 questions (50% simple/factual, 25% reasoning, 25% edge_case/multi-context)
- Faithfulness: 0.9444 | Answer Relevancy: 0.8475 | Context Precision: 0.8240 | Context Recall: 0.9108
- Total eval cost: ~$0.15
- Identified 3 failure clusters (xem `phase-a/failure_analysis.md`)

### Phase B — LLM-Judge (25 điểm)

- Cohen's kappa vs human: computed from 10 human-annotated pairs
- Position bias mitigated via swap-and-average
- Length bias quantified (B win rate when longer answer)

### Phase C — Guardrails (35 điểm)

- PII detection: Presidio + Vietnamese regex (CCCD, SĐT, MST, Email)
- Topic validator: LLM zero-shot + keyword fallback
- Adversarial defense: 20 attacks tested (DAN, roleplay, split, encoding, injection)
- Llama Guard 3 (API) / OpenAI Moderation fallback
- Latency benchmark: P50/P95/P99 measured

### Phase D — Blueprint (10 điểm)

- [blueprint.md](phase-d/blueprint.md) — 7 SLOs, architecture diagram (Mermaid), 4 incidents playbook, cost analysis

## Cấu trúc repo

```
lab24-eval-guardrails/
├── README.md                        # File này
├── requirements.txt                 # Dependencies
├── prompts.md                       # AI prompts đã dùng
│
├── phase-a/
│   ├── testset_v1.csv               # 55 questions (3 distributions)
│   ├── testset_review_notes.md      # Manual review 10+ questions
│   ├── ragas_results.csv            # 4 metrics per question
│   ├── ragas_summary.json           # Aggregate scores
│   └── failure_analysis.md          # Bottom 10 + clusters
│
├── phase-b/
│   ├── pairwise_results.csv         # Swap-and-average results
│   ├── absolute_scores.csv          # 4-dimension rubric scores
│   ├── human_labels.csv             # 10 human annotations
│   ├── kappa_analysis.py            # Cohen's kappa computation
│   └── judge_bias_report.md         # Position + length bias
│
├── phase-c/
│   ├── input_guard.py               # PII + Topic guardrails
│   ├── output_guard.py              # Llama Guard 3 / Moderation
│   ├── full_pipeline.py             # End-to-end guarded pipeline
│   ├── pii_test_results.csv         # PII detection test results
│   ├── adversarial_test_results.csv # 20 adversarial attack results
│   └── latency_benchmark.csv        # P50/P95/P99 per layer
│
├── phase-d/
│   └── blueprint.md                 # SLO + Arch + Playbook + Cost
│
├── .github/workflows/
│   └── eval-gate.yml                # CI/CD eval gate
│
├── src/                             # Core modules (from Day 18)
│   ├── m1_chunking.py
│   ├── m2_search.py
│   ├── m3_rerank.py
│   ├── m4_eval.py
│   ├── m5_enrichment.py
│   ├── m6_judge.py                  # LLM-as-Judge (Lab 24)
│   ├── m7_guardrails.py             # Guardrails stack (Lab 24)
│   └── pipeline.py
│
├── data/                            # Document corpus
├── reports/                         # Auto-generated reports
└── analysis/                        # Analysis documents
```

## Lessons Learned

1. **RAGAS evaluation** giúp phát hiện bottleneck thực sự của RAG — ví dụ faithfulness cao nhưng context_precision thấp cho thấy retriever lấy quá nhiều chunks rác, cần tăng chất lượng reranking thay vì sửa prompt.

2. **LLM-as-Judge có bias nghiêm trọng** — position bias (answer A thắng nhiều hơn khi liệt kê trước) và length bias (answer dài hơn thường được chọn). Swap-and-average là kỹ thuật đơn giản nhưng hiệu quả để mitigate.

3. **Guardrails là lớp defense cần thiết** — PII regex cho tiếng Việt (CCCD 12 số, SĐT 0xx) bổ sung cho Presidio chỉ support EN. Llama Guard 3 qua API là giải pháp khả thi khi không có GPU.

## Demo Video

[Link video demo 5 phút — TBD]
