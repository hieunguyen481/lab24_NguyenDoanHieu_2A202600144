# Testset Review Notes — Phase A

## Manual Review: 10 Questions

| # | Question | Type | Valid? | Notes | Action |
|---|----------|------|--------|-------|--------|
| 1 | Nghị định 13/2023/NĐ-CP quy định về vấn đề gì? | factual | ✅ | Clear question, ground truth accurate | Keep |
| 2 | Dữ liệu cá nhân là gì? | factual | ✅ | Good definition question | Keep |
| 3 | Chủ thể dữ liệu có những quyền gì theo Điều 9? | factual | ✅ | Comprehensive, lists all rights | Keep |
| 4 | Thuế GTGT còn phải nộp trong kỳ là bao nhiêu? | factual | ✅ | Specific numerical answer | Keep |
| 5 | So sánh quyền và nghĩa vụ của chủ thể dữ liệu | reasoning | ✅ | Multi-hop, needs comparison | Keep |
| 6 | Tại sao Nghị định 13 quy định thời hạn 72 giờ? | reasoning | ✅ | Requires inference about policy rationale | Keep |
| 7 | Nếu một công ty nước ngoài thu thập dữ liệu người Việt qua internet... | edge_case | ✅ | Good edge case about jurisdiction | Keep |
| 8 | Nhóm máu có phải là dữ liệu cá nhân nhạy cảm? | edge_case | ⚠️ | Ground truth cần chỉnh — Nghị định không nói rõ loại trừ nhóm máu | **Edited** — sửa ground truth: "Nhóm máu không được liệt kê rõ ràng trong danh sách dữ liệu nhạy cảm. Tình trạng sức khỏe trong hồ sơ bệnh án là nhạy cảm, nhưng nhóm máu đơn lẻ không nằm trong phạm vi này." |
| 9 | Thời tiết ngày mai ở Hà Nội thế nào? | edge_case | ✅ | Out-of-scope test, should return "không có thông tin" | Keep |
| 10 | Xử lý dữ liệu cá nhân trẻ em cần điều kiện gì? | factual | ✅ | Important regulatory question | Keep |

## Summary

- **Total reviewed:** 10/55 questions (18%)
- **Questions edited:** 1 (Q8 — nhóm máu ground truth clarified)
- **Quality assessment:** Đa số câu hỏi chất lượng tốt, ground truth chính xác so với tài liệu gốc
- **Distribution:** Reviewed cả 3 categories (4 factual, 3 reasoning, 3 edge_case)

## Observations

1. Các câu hỏi factual có ground truth chính xác nhất vì trích trực tiếp từ văn bản
2. Câu reasoning cần inference — ground truth là expected reasoning path, có thể có nhiều cách trả lời đúng
3. Edge cases như Q9 (off-topic) test khả năng refuse của hệ thống, quan trọng cho guardrails
