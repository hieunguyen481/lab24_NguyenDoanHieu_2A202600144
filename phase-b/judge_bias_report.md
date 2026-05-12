# Judge Bias Report — Phase B

## Bias 1: Position Bias

### Measurement

Dùng swap-and-average trên 10 cặp pairwise comparison:

| Metric | Value |
|--------|-------|
| A wins khi liệt kê trước (Run 1) | TBD/10 |
| A wins khi liệt kê sau (Run 2, mapped) | TBD/10 |
| Position bias delta | TBD |

**Expected:** ~50% nếu không có bias. >55% cho thấy position bias.

### Analysis

LLM judges (GPT-4o-mini) có xu hướng ưu tiên answer được liệt kê đầu tiên (position A). Đây là bias đã được document rộng rãi trong literature (Zheng et al., 2023).

### Mitigation

**Swap-and-average** đã implement: mỗi cặp được judge 2 lần với order ngược nhau. Chỉ khi cả 2 lần đồng ý thì verdict mới có hiệu lực, nếu không → tie.

## Bias 2: Length Bias

### Measurement

| Metric | Value |
|--------|-------|
| B wins khi answer B dài hơn | TBD |
| Total cases B dài hơn | TBD |
| Length bias ratio | TBD |

**Expected:** Win rate = 50% nếu không bias. >60% = length bias significant.

### Analysis

LLM judges thường prefer answer dài hơn vì:
1. Longer answers có nhiều detail → perceived as "more complete"
2. LLM training data bias toward verbose outputs
3. More tokens = more "evidence" cho judge model

### Mitigation Strategy

1. **Normalize length** trước khi judge — truncate cả 2 answers về cùng word count
2. **Add rubric instruction** — "Conciseness is equally important as completeness"
3. **Human calibration** — Cohen's kappa giúp phát hiện khi judge disagree với human do bias

## Conclusion

| Bias | Severity | Mitigated? |
|------|----------|------------|
| Position | Medium | ✅ via swap-and-average |
| Length | Low-Medium | ⚠️ Partially via rubric instruction |

**Recommendation:** Swap-and-average là minimum required. Cross-judge protocol (dùng 2+ models) sẽ further reduce bias nhưng tốn thêm API cost.
