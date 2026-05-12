# Failure Cluster Analysis — Phase A

## Bottom 10 Questions

| # | Question (truncated) | Type | F | AR | CP | CR | Avg | Cluster |
|---|---|---|---|---|---|---|---|---|
| 1 | "Cơ quan chuyên trách bảo vệ dữ liệu..." | factual | 0.50 | 0.70 | 0.60 | 0.80 | 0.65 | C1 |
| 2 | "Chủ thể dữ liệu có nghĩa vụ gì..." | factual | 0.80 | 0.75 | 0.50 | 0.40 | 0.61 | C2 |
| 3 | "Kỳ tính thuế trong tờ khai thuế GTGT..." | factual | 0.90 | 0.60 | 0.33 | 0.80 | 0.66 | C3 |
| 4 | "Nghị định 13 áp dụng cho những đối tượng..." | factual | 0.67 | 0.80 | 0.70 | 0.60 | 0.69 | C1 |
| 5 | "Khi nào có thể xử lý dữ liệu không cần đồng ý..." | factual | 0.70 | 0.80 | 0.60 | 0.40 | 0.63 | C2 |
| 6 | "So sánh quyền và nghĩa vụ của chủ thể..." | reasoning | 0.60 | 0.70 | 0.50 | 0.45 | 0.56 | C2 |
| 7 | "Phân tích chuỗi xử lý khi phát hiện vi phạm..." | reasoning | 0.55 | 0.65 | 0.40 | 0.50 | 0.53 | C2 |
| 8 | "Tỷ lệ thuế GTGT thực tế mà DHA Surfaces..." | reasoning | 0.80 | 0.50 | 0.60 | 0.70 | 0.65 | C3 |
| 9 | "Từ tờ khai thuế, DHA Surfaces có lãi hay lỗ..." | reasoning | 0.70 | 0.55 | 0.45 | 0.60 | 0.58 | C3 |
| 10 | "Nếu chủ thể dữ liệu đã chết, ai có quyền..." | edge_case | 0.40 | 0.60 | 0.50 | 0.30 | 0.45 | C2 |

## Clusters Identified

### Cluster C1: Hallucination — Generator fabricates information

**Pattern:** Faithfulness thấp (<0.70) dù context precision/recall OK. Generator thêm thông tin không có trong context.

**Examples:**
- "Cơ quan chuyên trách bảo vệ dữ liệu cá nhân..." → LLM bịa thêm chức năng không có trong văn bản
- "Nghị định 13 áp dụng cho những đối tượng nào?" → LLM thêm đối tượng ngoài quy định

**Root cause:** Prompt chưa đủ strict, LLM extrapolate dựa trên training knowledge thay vì chỉ dùng context.

**Proposed fix:**
- Thêm instruction trong system prompt: "Chỉ trả lời dựa trên thông tin có trong context. Nếu không tìm thấy, trả lời 'Không có thông tin trong tài liệu.'"
- Set `temperature=0` cho generation
- Thêm citation mechanism: yêu cầu LLM quote trực tiếp từ context

### Cluster C2: Multi-hop retrieval failures

**Pattern:** Context recall thấp (<0.50) cho các câu hỏi cần kết hợp thông tin từ nhiều chunks/điều khoản.

**Examples:**
- "Chủ thể dữ liệu có nghĩa vụ gì..." → Nghĩa vụ nằm rải rác ở nhiều điều, retriever chỉ lấy 1-2 chunks
- "So sánh quyền và nghĩa vụ..." → Cần cả 2 phần (quyền + nghĩa vụ) nhưng retriever ưu tiên 1 phần
- "Phân tích chuỗi xử lý khi phát hiện vi phạm..." → Quy trình trải 3-4 điều, chunks bị cắt rời
- "Nếu chủ thể dữ liệu đã chết, ai có quyền..." → Thông tin ở điều ít xuất hiện, BM25 rank thấp

**Root cause:** `RERANK_TOP_K=7` chưa đủ cho multi-hop queries. Chunking cắt giữa các điều khoản liên quan.

**Proposed fix:**
- Tăng `RERANK_TOP_K` từ 7 → 10 cho multi-hop queries
- Implement parent-child retrieval: khi match child chunk → kéo cả parent chunk
- Thêm query decomposition: split "so sánh A và B" thành 2 sub-queries
- Improve chunking: ensure mỗi Điều (Article) là 1 chunk đầy đủ

### Cluster C3: Cross-document confusion (Off-topic retrievals)

**Pattern:** Context precision thấp (<0.50) — retriever lấy chunks từ document sai (ví dụ: lẫn giữa Nghị định 13 và tờ khai thuế).

**Examples:**
- "Kỳ tính thuế trong tờ khai..." → Kết quả trộn lẫn chunks từ Nghị định 13
- "Tỷ lệ thuế GTGT thực tế..." → Cần tính toán từ tờ khai nhưng retriever lấy thêm chunks luật thuế
- "DHA Surfaces có lãi hay lỗ..." → Retriever lấy chunks không liên quan về thuế GTGT

**Root cause:** Hybrid search không phân biệt được document source. BM25 match keyword "thuế" từ cả 2 tài liệu.

**Proposed fix:**
- Thêm metadata filter theo `source` document khi query liên quan đến tài liệu cụ thể
- Implement Self-Query Retrieval để tự detect intent ("tờ khai" → filter `source=BCTC.md`)
- Tăng weight cho dense search trong RRF (semantic matching phân biệt context tốt hơn BM25)
