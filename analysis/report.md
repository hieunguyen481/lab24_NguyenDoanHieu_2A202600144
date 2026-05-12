# Báo cáo Lab 24: Production RAG Evaluation & Guardrails Stack

**Học viên:** Nguyễn Doãn Hiếu-2A202600144
**Điểm hệ thống tự chấm:** 100/100 

---

## 1. Tổng quan (Overview)
Dự án này là bước nâng cấp từ Lab 18, biến một RAG pipeline cơ bản thành một hệ thống Production-Ready. Hệ thống được trang bị đầy đủ các lớp đánh giá tự động (RAGAS, LLM-as-a-Judge) và hệ thống rào chắn (Guardrails) đa lớp để đảm bảo tính an toàn, bảo mật dữ liệu PII và chống lại các cuộc tấn công Prompt Injection.

---

## 2. Kết quả Đánh giá (Evaluation Results)

### Phase A: RAGAS Evaluation
Thực hiện đánh giá trên tập dữ liệu tổng hợp gồm **52 câu hỏi** (phân bổ: 26 Factual, 13 Reasoning, 13 Edge Cases).

*   **Context Precision:** 0.8512 ✅ *(Vượt mức 0.70)*
*   **Context Recall:** 0.7949 ✅ *(Vượt mức 0.75)*
*   **Faithfulness:** 0.7191 ⚠️ *(Chưa đạt mức 0.85 - LLM đôi khi bị hallucination hoặc trả lời thiếu chính xác so với context)*
*   **Answer Relevancy:** 0.7159 ⚠️ *(Chưa đạt mức 0.80 - Câu trả lời đôi khi bị lan man)*

### Phase B: LLM-as-a-Judge
Thực hiện đánh giá Pairwise và Absolute cho **30 câu hỏi** giữa Naive Baseline và Production RAG.

*   **Tỉ lệ chiến thắng (Win Rate):**
    *   Production RAG (B) thắng: 8 lần (Tỉ lệ 26.67%)
    *   Hòa (Tie): 22 lần
    *   Naive Baseline (A) thắng: 0 lần
*   **Đánh giá thiên kiến (Bias Mitigation):** 
    *   Đã áp dụng kỹ thuật **Swap-and-Average**. Độ lệch thiên kiến (Bias Delta): **0.1000**.
*   **Độ đồng thuận với con người (Cohen's Kappa):** 
    *   $\kappa = 0.1566$ (Mức độ Slight).

### Phase C: Guardrails Stack
Hệ thống bảo vệ hoạt động hiệu quả với 4 lớp phòng thủ:

*   **L1 - PII Detection (Presidio + Vietnamese Regex):** Nhận diện xuất sắc các mẫu PII đặc thù của Việt Nam (CCCD, Mã số thuế, SĐT).
*   **L2 - Topic Validator (LLM-based):** Phân loại và từ chối chính xác các câu hỏi lạc đề.
*   **L3 - Adversarial Testing:** Đánh chặn thành công **20/20 (100%)** các kịch bản tấn công (Prompt injection, harmful, off-topic, pii extraction). Tổng Accuracy đạt **80.00%**.
*   **L4 - Latency Benchmark:** P95 Latency của toàn bộ pipeline đo được là **10.169 giây**.

---

## 3. Kiến trúc Production (Blueprint Phase D)
Hệ thống áp dụng kiến trúc **Defense-in-Depth** 4 lớp: Input, Generation, Output, và Audit. Đã định nghĩa bộ **SLO (Service Level Objectives)** khắt khe cùng với Playbook ứng phó sự cố được đính kèm chi tiết trong `analysis/blueprint.md`.

---

## 4. Bài học rút ra (Lessons Learned)
1.  **Guardrails đánh đổi bằng Latency:** Tích hợp LLM vào Guardrails tăng đáng kể độ trễ của hệ thống (P95 ~10s).
2.  **LLM-Judge rất nhạy cảm với Prompt:** Việc thiết kế Prompt cho Judge để nó không chọn bừa "Tie" là một nghệ thuật.
3.  **Presidio cần Customize mạnh cho tiếng Việt:** Mặc định Presidio không hỗ trợ tiếng Việt. Việc viết Regex kết hợp với Presidio tiếng Anh giúp hệ thống hoạt động hoàn hảo.
