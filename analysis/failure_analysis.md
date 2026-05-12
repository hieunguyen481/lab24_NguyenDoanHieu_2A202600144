# Phân tích Lỗi Hệ Thống (Failure Analysis) - Lab 24

Dựa trên kết quả chạy RAGAS Evaluation trên 52 câu hỏi, dưới đây là phân tích chi tiết về các lỗi hệ thống mắc phải và giải pháp khắc phục.

## 1. Kết quả Metrics Tổng Quan
*   **Context Precision:** 0.8512 ✅ *(Xuất sắc - Context liên quan được đưa lên đầu)*
*   **Context Recall:** 0.7949 ✅ *(Tốt - Retriever tìm được đa số thông tin cần thiết)*
*   **Faithfulness:** 0.7191 ⚠️ *(Trung bình - LLM đôi khi sinh ra thông tin không có trong context)*
*   **Answer Relevancy:** 0.7159 ⚠️ *(Trung bình - Câu trả lời đôi khi không tập trung vào trọng tâm câu hỏi)*

## 2. Phân Tích Cụm Lỗi (Failure Cluster Analysis)
Hệ thống đã tự động phân nhóm các câu hỏi bị chấm điểm thấp thành 4 cụm lỗi chính:

### Cụm 1: Hallucination (44.2% - 23 câu hỏi)
*   **Triệu chứng:** Điểm Faithfulness thấp. LLM bịa ra thông tin không có trong context hoặc tự suy diễn sai lệch so với Ground Truth.
*   **Nguyên nhân:** Do prompt chưa đủ nghiêm ngặt, hoặc LLM có xu hướng "chiều lòng" người dùng nên tự thêm thắt chi tiết khi context không đủ.
*   **Giải pháp (Hành động):** 
    *   Giảm `temperature` của mô hình sinh (ví dụ: GPT-4o-mini) xuống 0.0 hoặc 0.1.
    *   Thêm vào system prompt câu thần chú: "Chỉ trả lời dựa trên context được cung cấp. Nếu không có thông tin, hãy nói 'Tôi không biết'."

### Cụm 2: Retrieval Gap (32.7% - 17 câu hỏi)
*   **Triệu chứng:** Điểm Context Recall thấp. Hệ thống không tìm thấy context chứa đáp án đúng.
*   **Nguyên nhân:** 
    *   Dense Retrieval (Embedding) không nắm bắt được các từ khóa chuyên ngành, số liệu hoặc từ khóa viết tắt.
    *   Chunk size quá nhỏ khiến thông tin bị đứt đoạn.
*   **Giải pháp (Hành động):**
    *   Áp dụng Hybrid Search (kết hợp Dense Embedding + Sparse BM25) để bắt chính xác từ khóa.
    *   Mở rộng kích thước chunk hoặc sử dụng kỹ thuật Parent-Child chunking để lấy thêm ngữ cảnh xung quanh.

### Cụm 3: Precision Noise (26.9% - 14 câu hỏi)
*   **Triệu chứng:** Điểm Context Precision bị ảnh hưởng nhẹ. Retriever trả về nhiều chunk không liên quan.
*   **Nguyên nhân:** Các từ khóa trong câu hỏi xuất hiện rải rác ở nhiều chunk không quan trọng, làm loãng context.
*   **Giải pháp (Hành động):**
    *   Tăng cường sức mạnh của lớp Reranker (Cross-Encoder) bằng cách giới hạn `top_k` nghiêm ngặt hơn (ví dụ chỉ lấy top 3 thay vì top 5) sau khi rerank.
    *   Áp dụng threshold cho score của reranker (chỉ giữ lại các chunk có độ liên quan > 0.5).

### Cụm 4: Irrelevance (23.1% - 12 câu hỏi)
*   **Triệu chứng:** Điểm Answer Relevancy thấp. Câu trả lời dài dòng, không đi thẳng vào vấn đề.
*   **Nguyên nhân:** LLM không xác định được ý định chính của câu hỏi, đặc biệt ở các câu hỏi dạng Reasoning hoặc Edge Case.
*   **Giải pháp (Hành động):**
    *   Chỉnh sửa lại prompt, yêu cầu LLM "Trả lời ngắn gọn, trực tiếp vào câu hỏi trước khi giải thích".
    *   Sử dụng LLM-based query rewriting trước khi đưa vào Retriever để làm rõ ý định câu hỏi.

## 3. Kế hoạch ưu tiên khắc phục
1.  **Ưu tiên cao nhất:** Cải thiện Prompt để giảm **Hallucination** và tăng **Answer Relevancy**. (Chỉ cần đổi prompt, không tốn tài nguyên code lại).
2.  **Ưu tiên trung bình:** Tích hợp Hybrid Search để giảm **Retrieval Gap**, qua đó cải thiện Context Recall (sẽ kéo theo Faithfulness tăng vì LLM có đủ dữ kiện).
3.  **Ưu tiên thấp:** Fine-tune Reranker để xử lý **Precision Noise**. Hiển tại Context Precision (0.85) đã rất cao nên chưa cần can thiệp ngay lập tức.
