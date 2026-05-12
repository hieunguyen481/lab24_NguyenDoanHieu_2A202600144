# AI Prompts Log — Lab 24

## Academic Integrity Declaration

Tôi đã sử dụng AI assistant (Gemini / Claude) trong quá trình làm lab. Dưới đây là log các prompts chính đã dùng.

## Prompts Used

### 1. Project Setup & Planning
- **Prompt:** "Từ yêu cầu Lab 24, tạo implementation plan cho project Day 23 từ gốc Day 18"
- **Purpose:** Lên kế hoạch cấu trúc project, xác định deliverables
- **Output used:** Implementation plan, task tracker

### 2. Test Set Expansion
- **Prompt:** "Expand test_set.json lên 50+ questions với 3 distributions (factual, reasoning, edge_case)"
- **Purpose:** Tạo synthetic test set cho RAGAS evaluation
- **Output used:** 55 questions trong test_set.json
- **Human review:** 10 questions reviewed manually, 1 question ground truth edited (Q8)

### 3. Module Development
- **Prompt:** "Tạo m6_judge.py cho LLM-as-Judge pipeline với pairwise, absolute, swap-and-average, Cohen kappa"
- **Purpose:** Build judge pipeline
- **Output used:** m6_judge.py module
- **Modifications:** Adjusted prompt templates cho Vietnamese context

### 4. Guardrails Implementation
- **Prompt:** "Tạo m7_guardrails.py với Presidio PII detection, topic validator, Llama Guard 3, latency measurement"
- **Purpose:** Build guardrail stack
- **Output used:** m7_guardrails.py module
- **Modifications:** Added Vietnamese PII patterns (CCCD, SĐT, MST)

### 5. Blueprint & Documentation
- **Prompt:** "Tạo blueprint.md với SLO, architecture Mermaid diagram, alert playbook, cost analysis"
- **Purpose:** Production readiness documentation
- **Output used:** analysis/blueprint.md

### 6. Bug Fixing
- **Prompt:** "Fix regex version incompatibility error"
- **Purpose:** Resolve `regex>=2025.10.22` requirement
- **Output used:** `pip install regex --upgrade`

## Diff: AI-generated vs Final

Các file AI-generated đều đã được review và chỉnh sửa:
- **test_set.json:** 1 question ground truth edited manually
- **m7_guardrails.py:** Vietnamese PII patterns tuned cho CCCD 12-digit format
- **blueprint.md:** SLO thresholds adjusted based on actual RAGAS scores from Day 18
- **adversarial_test_set.json:** Thêm Vietnamese-specific jailbreak attempts
