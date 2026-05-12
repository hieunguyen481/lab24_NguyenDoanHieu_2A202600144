"""
Module 7: Guardrails — PII Detection, Topic Validation, Content Safety, Latency.

Lab 24 Phase C: Production guardrail stack for RAG pipeline.
"""

import os, sys, re, json, time
from dataclasses import dataclass, field

sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ALLOWED_TOPICS, PII_PATTERNS_VN, JUDGE_MODEL


@dataclass
class GuardrailResult:
    passed: bool
    check_type: str  # "pii", "topic", "safety"
    details: dict = field(default_factory=dict)
    message: str = ""


import logging
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# Suppress presidio warnings
logging.getLogger("presidio-analyzer").setLevel(logging.ERROR)

# Global instances to avoid re-initialization overhead and spam
_analyzer = None
_anonymizer = None

def get_analyzer():
    global _analyzer
    if _analyzer is None:
        try:
            _analyzer = AnalyzerEngine()
        except Exception:
            pass
    return _analyzer

def get_anonymizer():
    global _anonymizer
    if _anonymizer is None:
        try:
            _anonymizer = AnonymizerEngine()
        except Exception:
            pass
    return _anonymizer

# ─── 1. Presidio PII Detection ──────────────────────────


def detect_pii(text: str) -> GuardrailResult:
    """
    Detect PII in text using Presidio + Vietnamese custom patterns.
    Returns GuardrailResult with detected entities.
    """
    detected = []

    # Vietnamese custom patterns
    for name, pattern in PII_PATTERNS_VN.items():
        matches = re.findall(pattern, text)
        for m in matches:
            match_text = m if isinstance(m, str) else m[0]
            detected.append({"type": name, "text": match_text, "source": "regex_vn"})

    # Presidio for English entities
    try:
        analyzer = get_analyzer()
        if analyzer:
            results = analyzer.analyze(text=text, language="en",
                                       entities=["PHONE_NUMBER", "EMAIL_ADDRESS",
                                                 "CREDIT_CARD", "PERSON", "LOCATION"])
            for r in results:
                detected.append({
                    "type": r.entity_type,
                    "text": text[r.start:r.end],
                    "score": r.score,
                    "source": "presidio",
                })
    except Exception as e:
        detected.append({"type": "ERROR", "text": str(e), "source": "presidio"})

    has_pii = len(detected) > 0
    return GuardrailResult(
        passed=not has_pii,
        check_type="pii",
        details={"entities": detected, "count": len(detected)},
        message=f"Detected {len(detected)} PII entities" if has_pii else "No PII detected",
    )


def redact_pii(text: str) -> str:
    """Redact detected PII from text."""
    result = text
    for name, pattern in PII_PATTERNS_VN.items():
        result = re.sub(pattern, f"[{name}_REDACTED]", result)

    try:
        analyzer = get_analyzer()
        anonymizer = get_anonymizer()
        if analyzer and anonymizer:
            analysis = analyzer.analyze(text=result, language="en",
                                        entities=["PHONE_NUMBER", "EMAIL_ADDRESS",
                                                  "CREDIT_CARD", "PERSON"])
            anonymized = anonymizer.anonymize(text=result, analyzer_results=analysis)
            result = anonymized.text
    except Exception:
        pass

    return result


# ─── 2. Topic Validator ──────────────────────────────────


def validate_topic(query: str) -> GuardrailResult:
    """
    Validate if query is on-topic using keyword matching first (fast),
    falls back to LLM classification for ambiguous cases.
    """
    query_lower = query.lower()

    # Fast path: keyword matching first (no API call needed)
    matched_topic = None
    for topic in ALLOWED_TOPICS:
        if topic.lower() in query_lower:
            matched_topic = topic
            break

    if matched_topic:
        return GuardrailResult(passed=True, check_type="topic",
                               details={"detected_topic": matched_topic, "method": "keyword"},
                               message=f"On-topic (keyword: {matched_topic})")

    # Check for obvious off-topic patterns
    off_topic_keywords = [
        "nấu", "phở", "bóng đá", "world cup", "thơ", "iphone", "sửa lỗi",
        "phương trình", "thời tiết", "game", "phim", "nhạc", "du lịch",
        "recipe", "weather", "sports", "movie", "music",
    ]
    for kw in off_topic_keywords:
        if kw in query_lower:
            return GuardrailResult(passed=False, check_type="topic",
                                   details={"detected_keyword": kw, "method": "keyword_reject"},
                                   message=f"Off-topic: matched '{kw}'")

    # LLM classification for ambiguous cases (with timeout)
    try:
        from openai import OpenAI
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError()
        client = OpenAI(timeout=10.0)
        topics_str = ", ".join(ALLOWED_TOPICS)
        resp = client.chat.completions.create(
            model=JUDGE_MODEL,
            messages=[
                {"role": "system", "content": f"Phân loại câu hỏi. Các chủ đề hợp lệ: {topics_str}. "
                 "Trả về JSON: {\"on_topic\": true/false, \"detected_topic\": \"...\", \"reason\": \"...\"}"},
                {"role": "user", "content": query},
            ],
            max_tokens=100,
            temperature=0.0,
        )
        data = json.loads(resp.choices[0].message.content.strip())
        on_topic = data.get("on_topic", False)
        return GuardrailResult(
            passed=on_topic,
            check_type="topic",
            details=data,
            message="On-topic" if on_topic else f"Off-topic: {data.get('reason', 'N/A')}",
        )
    except Exception:
        # Default: allow (avoid blocking legitimate queries)
        return GuardrailResult(passed=True, check_type="topic",
                               details={"method": "fallback_allow"},
                               message="Topic check: fallback allow")


# ─── 3. Llama Guard 3 Content Safety ────────────────────


UNSAFE_KEYWORDS = [
    "hack", "exploit", "bypass", "ignore instructions",
    "bỏ qua hướng dẫn", "giả vờ", "pretend", "jailbreak",
    "tấn công", "phá hoại", "vũ khí", "chất nổ",
]


def check_content_safety(text: str) -> GuardrailResult:
    """
    Check content safety using Llama Guard 3 API or keyword fallback.
    Tries Together AI / HuggingFace API first, falls back to keyword filter.
    """
    # Try Together AI / HuggingFace
    try:
        together_key = os.environ.get("TOGETHER_API_KEY", "")
        if together_key:
            import requests
            resp = requests.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={"Authorization": f"Bearer {together_key}"},
                json={
                    "model": "meta-llama/Meta-Llama-Guard-3-8B",
                    "messages": [{"role": "user", "content": text}],
                    "max_tokens": 100,
                },
                timeout=30,
            )
            data = resp.json()
            output = data["choices"][0]["message"]["content"].strip()
            is_safe = output.lower().startswith("safe")
            categories = []
            if not is_safe:
                lines = output.split("\n")
                categories = [l.strip() for l in lines[1:] if l.strip()]
            return GuardrailResult(
                passed=is_safe,
                check_type="safety",
                details={"model": "llama-guard-3", "raw_output": output,
                          "violated_categories": categories},
                message="Safe" if is_safe else f"Unsafe: {', '.join(categories)}",
            )
    except Exception:
        pass

    # Try OpenAI moderation as alternative
    try:
        from openai import OpenAI
        if os.environ.get("OPENAI_API_KEY"):
            client = OpenAI()
            mod = client.moderations.create(input=text)
            flagged = mod.results[0].flagged
            categories = {k: v for k, v in mod.results[0].categories.__dict__.items() if v}
            return GuardrailResult(
                passed=not flagged,
                check_type="safety",
                details={"model": "openai-moderation", "flagged_categories": categories},
                message="Safe" if not flagged else f"Flagged: {list(categories.keys())}",
            )
    except Exception:
        pass

    # Fallback: keyword filter
    text_lower = text.lower()
    found = [kw for kw in UNSAFE_KEYWORDS if kw in text_lower]
    is_safe = len(found) == 0
    return GuardrailResult(
        passed=is_safe,
        check_type="safety",
        details={"method": "keyword_filter", "matched_keywords": found},
        message="Safe" if is_safe else f"Unsafe keywords: {found}",
    )


# ─── 4. Combined Guardrail Check ────────────────────────


def run_guardrails(query: str, response: str = "") -> dict:
    """
    Run all guardrail checks on query and response.
    Returns combined result.
    """
    results = {}

    # Input guardrails
    results["input_pii"] = detect_pii(query)
    results["topic"] = validate_topic(query)
    results["input_safety"] = check_content_safety(query)

    # Output guardrails (if response provided)
    if response:
        results["output_pii"] = detect_pii(response)
        results["output_safety"] = check_content_safety(response)

    all_passed = all(r.passed for r in results.values())
    return {
        "passed": all_passed,
        "checks": {k: {"passed": v.passed, "message": v.message,
                        "details": v.details} for k, v in results.items()},
    }


# ─── 5. Latency Measurement ─────────────────────────────


def measure_latency(pipeline_fn, queries: list[str], n_runs: int = 1) -> dict:
    """
    Measure P50/P95/P99 latency for pipeline function.

    Args:
        pipeline_fn: Callable that takes query string and returns (answer, contexts)
        queries: List of query strings
        n_runs: Number of runs per query

    Returns:
        Latency statistics dict.
    """
    latencies = []

    for q in queries:
        for _ in range(n_runs):
            start = time.perf_counter()
            try:
                pipeline_fn(q)
            except Exception:
                pass
            elapsed = time.perf_counter() - start
            latencies.append(elapsed)

    if not latencies:
        return {"p50": 0, "p95": 0, "p99": 0, "mean": 0, "count": 0}

    latencies.sort()
    n = len(latencies)

    def percentile(p):
        idx = int(n * p / 100)
        return latencies[min(idx, n - 1)]

    report = {
        "p50_s": round(percentile(50), 4),
        "p95_s": round(percentile(95), 4),
        "p99_s": round(percentile(99), 4),
        "mean_s": round(sum(latencies) / n, 4),
        "min_s": round(min(latencies), 4),
        "max_s": round(max(latencies), 4),
        "count": n,
    }
    return report


# ─── 6. Adversarial Test Runner ──────────────────────────


def run_adversarial_tests(test_set_path: str, pipeline_fn=None) -> dict:
    """
    Run adversarial test set through guardrails.

    Args:
        test_set_path: Path to adversarial_test_set.json
        pipeline_fn: Optional pipeline function to also test responses

    Returns:
        Adversarial test report.
    """
    with open(test_set_path, encoding="utf-8") as f:
        tests = json.load(f)

    results = []
    blocked = 0
    total = len(tests)

    for i, test in enumerate(tests):
        query = test["query"]
        category = test.get("category", "unknown")
        expected_block = test.get("should_block", True)

        print(f"  [Adversarial {i+1}/{total}] [{category}] {query[:50]}...")

        guardrail_result = run_guardrails(query)
        was_blocked = not guardrail_result["passed"]
        if was_blocked:
            blocked += 1

        results.append({
            "query": query,
            "category": category,
            "expected_block": expected_block,
            "was_blocked": was_blocked,
            "correct": was_blocked == expected_block,
            "details": guardrail_result["checks"],
        })

    correct = sum(1 for r in results if r["correct"])
    report = {
        "total": total,
        "blocked": blocked,
        "allowed": total - blocked,
        "accuracy": round(correct / max(total, 1), 4),
        "by_category": {},
        "results": results,
    }

    # Aggregate by category
    categories = set(r["category"] for r in results)
    for cat in categories:
        cat_results = [r for r in results if r["category"] == cat]
        report["by_category"][cat] = {
            "total": len(cat_results),
            "blocked": sum(1 for r in cat_results if r["was_blocked"]),
            "accuracy": round(sum(1 for r in cat_results if r["correct"]) / len(cat_results), 4),
        }

    # Save report
    os.makedirs("reports", exist_ok=True)
    with open("reports/guardrail_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    print(f"  Guardrail report saved to reports/guardrail_report.json")

    # Export to CSV for Phase C rubric
    import csv
    os.makedirs("phase-c", exist_ok=True)
    with open("phase-c/adversarial_test_results.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = ["query", "category", "expected_block", "was_blocked", "correct"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for res in results:
            writer.writerow({
                "query": res["query"],
                "category": res["category"],
                "expected_block": res["expected_block"],
                "was_blocked": res["was_blocked"],
                "correct": res["correct"]
            })
    print(f"  Adversarial results saved to phase-c/adversarial_test_results.csv")

    return report


if __name__ == "__main__":
    print("=== Guardrails Module ===")
    # Quick test
    print("\n--- PII Test ---")
    r = detect_pii("Số CCCD: 012345678901, SĐT: 0912345678")
    print(f"  PII detected: {r.details}")

    print("\n--- Topic Test ---")
    r = validate_topic("Nghị định 13 quy định gì?")
    print(f"  Topic: {r.message}")

    print("\n--- Safety Test ---")
    r = check_content_safety("Cách hack hệ thống")
    print(f"  Safety: {r.message}")
