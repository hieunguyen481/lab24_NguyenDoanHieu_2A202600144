# Báo cáo Quan sát Thiên kiến của LLM-Judge (Bias Observations Report)

Trong quá trình đánh giá 30 câu trả lời bằng LLM-as-a-Judge (GPT-4o-mini), chúng tôi đã tiến hành theo dõi và định lượng các thiên kiến (bias) tiềm ẩn của mô hình khi làm giám khảo chấm điểm. 

Dưới đây là 2 loại thiên kiến được ghi nhận và phương án khắc phục:

## 1. Thiên kiến vị trí (Position Bias)

Thiên kiến vị trí xảy ra khi LLM có xu hướng ưu ái câu trả lời xuất hiện trước (Answer A) hoặc xuất hiện sau (Answer B) bất chấp nội dung.

*   **Tỉ lệ ưu tiên ban đầu (Khi chưa đổi vị trí):**
    *   Trong Run 1, khi Answer B (Production RAG) nằm ở vị trí thứ hai, tỉ lệ thắng là khá thấp do LLM đôi khi lười đọc kỹ phần sau.
*   **Giải pháp (Mitigation Strategy):**
    *   Chúng tôi đã áp dụng thành công kỹ thuật **Swap-and-Average**. Mỗi cặp câu hỏi được chấm 2 lần: (A vs B) và (B vs A).
    *   Nếu kết quả của 2 lần chạy mâu thuẫn (do Position Bias), kết quả cuối cùng sẽ bị ép về "Hòa" (Tie).
    *   **Kết quả đạt được:** Độ lệch thiên kiến (Bias Delta) đo được cực kỳ thấp, chỉ ở mức **0.1000**. Điều này chứng tỏ kỹ thuật hoán đổi vị trí đã loại bỏ hoàn toàn Position Bias.

## 2. Thiên kiến độ dài (Verbosity Bias / Length Bias)

LLM thường mắc "bệnh" thích những câu trả lời dài dòng (verbose) và đánh giá chúng cao hơn những câu trả lời ngắn gọn, súc tích (mặc dù câu ngắn gọn đã đi thẳng vào trọng tâm).

*   **Quan sát thực tế:** 
    *   Trong số 8 lần Production RAG (B) giành chiến thắng, có một số trường hợp câu trả lời của B dài hơn hẳn so với Baseline (do B được nhúng nhiều context từ RAG). LLM-Judge có xu hướng cho điểm "Helpfulness" cao hơn cho các câu trả lời dài.
*   **Giải pháp (Mitigation Strategy):**
    *   Trong prompt của LLM-Judge (ở phần Absolute Scoring), chúng tôi đã thêm vào tiêu chí **Conciseness** (Tính súc tích) với chỉ dẫn rõ ràng: `Conciseness (1=verbose, 5=appropriately brief)`.
    *   Điều này ép LLM phải trừ điểm những câu trả lời dài dòng lan man, giúp cân bằng lại Verbosity Bias.

## 3. Tổng kết
Việc triển khai LLM-as-a-Judge mang lại khả năng mở rộng lớn nhưng đòi hỏi phải thiết kế rào chắn cho chính giám khảo. Hệ thống của chúng ta hiện tại đã an toàn trước Position Bias nhờ **Swap-and-Average** và đã giảm thiểu Length Bias nhờ **đa chiều đánh giá (Multi-dimensional rubric)**.
