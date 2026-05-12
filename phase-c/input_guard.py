"""
Phase C — Input Guard: PII Redaction + Topic Validator

Combines Presidio NER (EN) + Vietnamese custom regex.
"""
import re, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

VN_PII = {
    "CCCD": r"\b\d{12}\b",
    "PHONE_VN": r"(\+84|0)\d{9,10}",
    "TAX_CODE": r"\b\d{10}(-\d{3})?\b",
    "EMAIL": r"\b[\w.-]+@[\w.-]+\.\w+\b",
}


class InputGuard:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

    def scrub_vn(self, t):
        """Layer 1: VN-specific regex."""
        found = []
        for name, pattern in VN_PII.items():
            matches = re.findall(pattern, t)
            for m in matches:
                match_text = m if isinstance(m, str) else m[0]
                found.append({"type": name, "text": match_text})
            t = re.sub(pattern, f"[{name}]", t)
        return t, found

    def scrub_ner(self, t):
        """Layer 2: Presidio NER (multilingual)."""
        results = self.analyzer.analyze(text=t, language="en")
        found = [{"type": r.entity_type, "text": t[r.start:r.end], "score": r.score} for r in results]
        anonymized = self.anonymizer.anonymize(text=t, analyzer_results=results)
        return anonymized.text, found

    def sanitize(self, t):
        """Full pipeline with latency tracking."""
        start = time.perf_counter()
        t, vn_found = self.scrub_vn(t)
        t, ner_found = self.scrub_ner(t)
        latency_ms = (time.perf_counter() - start) * 1000
        all_found = vn_found + ner_found
        return t, latency_ms, all_found


class TopicGuard:
    """Topic validator using LLM zero-shot classification."""
    def __init__(self, allowed_topics):
        self.topics = allowed_topics

    def check(self, text):
        """Check if query is on-topic. Returns (bool, reason)."""
        try:
            from openai import OpenAI
            client = OpenAI()
            topics_str = ", ".join(self.topics)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Is this question about one of these topics: {topics_str}? Answer YES or NO only."},
                    {"role": "user", "content": text},
                ],
                max_tokens=10, temperature=0.0,
            )
            answer = resp.choices[0].message.content.strip()
            is_on = answer.upper().startswith("YES")
            return is_on, f"{'On-topic' if is_on else 'Off-topic'}: {answer}"
        except Exception:
            # Fallback: keyword matching
            text_lower = text.lower()
            for topic in self.topics:
                if topic.lower() in text_lower:
                    return True, f"On-topic (keyword: {topic})"
            return True, "Topic check: fallback allow"


if __name__ == "__main__":
    import csv
    guard = InputGuard()

    test_inputs = [
        "Hi, I'm John Smith from Microsoft. Email: john@ms.com",
        "Call me at +1-555-1234 or visit 123 Main Street, NYC",
        "Số CCCD của tôi là 012345678901",
        "Liên hệ qua 0987654321 hoặc tax 0123456789-001",
        "Customer Nguyễn Văn A, CCCD 098765432101, phone 0912345678",
        "",
        "Just a normal question",
        "A" * 5000,
        "Lý Văn Bình ở 123 Lê Lợi",
        "tax_code:0123456789-001 cccd:012345678901",
    ]

    results = []
    for inp in test_inputs:
        output, latency, found = guard.sanitize(inp)
        results.append({
            "input": inp[:100],
            "output": output[:100],
            "pii_found": len(found),
            "pii_types": [f["type"] for f in found],
            "latency_ms": round(latency, 2),
        })
        print(f"  PII={len(found):2d} | {latency:6.1f}ms | {inp[:60]}...")

    # Save CSV
    os.makedirs("phase-c", exist_ok=True)
    with open("phase-c/pii_test_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["input", "output", "pii_found", "pii_types", "latency_ms"])
        writer.writeheader()
        writer.writerows(results)
    print("\nSaved phase-c/pii_test_results.csv")
