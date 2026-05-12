"""
Phase C — Full Stack Integration & Latency Benchmark

End-to-end guarded pipeline: L1 → L2 → L3 → L4 with per-layer timing.
"""
import time, json, os, sys, csv
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def guarded_pipeline(user_input, search, reranker, input_guard, topic_guard, output_guard):
    """
    Full stack with per-layer latency tracking.
    
    Architecture:
        [L1] Input Layer (PII + Topic) → [L2] RAG LLM → [L3] Output Guard → [L4] Audit Log
    """
    timings = {}

    # L1: Input Guards (PII + Topic)
    t0 = time.perf_counter()
    sanitized, pii_latency, pii_found = input_guard.sanitize(user_input)
    topic_ok, topic_reason = topic_guard.check(sanitized)
    timings["L1"] = (time.perf_counter() - t0) * 1000

    if not topic_ok:
        return f"Xin lỗi, câu hỏi của bạn nằm ngoài phạm vi hỗ trợ. {topic_reason}", timings, False

    # L2: RAG Pipeline (Day 18)
    t0 = time.perf_counter()
    from src.pipeline import run_query
    answer, contexts = run_query(sanitized, search, reranker)
    timings["L2"] = (time.perf_counter() - t0) * 1000

    # L3: Output Guard (Llama Guard / Moderation)
    t0 = time.perf_counter()
    is_safe, safety_result, safety_latency = output_guard.check(sanitized, answer)
    timings["L3"] = (time.perf_counter() - t0) * 1000

    if not is_safe:
        return "Xin lỗi, hệ thống phát hiện nội dung không phù hợp trong câu trả lời.", timings, False

    # L4: Audit Log (async in production, sync here for simplicity)
    t0 = time.perf_counter()
    audit_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "query": user_input[:100],
        "pii_found": len(pii_found),
        "topic_ok": topic_ok,
        "is_safe": is_safe,
        "timings": timings,
    }
    timings["L4"] = (time.perf_counter() - t0) * 1000

    timings["total"] = sum(timings[l] for l in ["L1", "L2", "L3"])

    return answer, timings, True


def benchmark(n_queries=50):
    """Benchmark full stack latency on n queries."""
    from src.pipeline import build_pipeline
    from src.m4_eval import load_test_set
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from input_guard import InputGuard, TopicGuard
    from output_guard import OutputGuardAPI

    print(f"\n=== Full Stack Latency Benchmark ({n_queries} queries) ===\n")

    # Build components
    search, reranker = build_pipeline()
    input_guard = InputGuard()
    topic_guard = TopicGuard([
        "pháp luật", "thuế", "dữ liệu cá nhân", "tài chính",
        "bảo vệ dữ liệu", "nghị định", "quy định", "doanh nghiệp",
    ])
    output_guard = OutputGuardAPI()

    # Load queries
    test_set = load_test_set()
    queries = [item["question"] for item in test_set[:n_queries]]

    all_timings = []
    for i, q in enumerate(queries):
        answer, timings, ok = guarded_pipeline(q, search, reranker, input_guard, topic_guard, output_guard)
        all_timings.append(timings)
        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(queries)}] completed")

    # Compute P50/P95/P99
    print("\n--- Per-Layer Latency ---")
    results = {}
    for layer in ["L1", "L2", "L3", "total"]:
        vals = [t.get(layer, 0) for t in all_timings if layer in t]
        if vals:
            results[layer] = {
                "P50_ms": round(np.percentile(vals, 50), 1),
                "P95_ms": round(np.percentile(vals, 95), 1),
                "P99_ms": round(np.percentile(vals, 99), 1),
                "mean_ms": round(np.mean(vals), 1),
            }
            print(f"  {layer}: P50={results[layer]['P50_ms']:.0f}ms, "
                  f"P95={results[layer]['P95_ms']:.0f}ms, "
                  f"P99={results[layer]['P99_ms']:.0f}ms")

    # Save CSV
    os.makedirs("phase-c", exist_ok=True)
    with open("phase-c/latency_benchmark.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["layer", "P50_ms", "P95_ms", "P99_ms", "mean_ms"])
        for layer, vals in results.items():
            writer.writerow([layer, vals["P50_ms"], vals["P95_ms"], vals["P99_ms"], vals["mean_ms"]])

    print(f"\nSaved phase-c/latency_benchmark.csv")

    # Check SLO
    l1_p95 = results.get("L1", {}).get("P95_ms", 0)
    l3_p95 = results.get("L3", {}).get("P95_ms", 0)
    print(f"\nSLO Check:")
    print(f"  L1 P95 {'✅' if l1_p95 < 50 else '⚠️'} {l1_p95:.0f}ms (target <50ms)")
    print(f"  L3 P95 {'✅' if l3_p95 < 100 else '⚠️'} {l3_p95:.0f}ms (target <100ms)")

    return results


if __name__ == "__main__":
    benchmark()
