"""
Lab 24 — Validation Script
============================
Kiểm tra deliverables theo rubric trước khi submit.
Chạy: python check_lab24.py
"""

import json, os, sys

sys.stdout.reconfigure(encoding='utf-8')


def check_file(path, required=True):
    if os.path.exists(path):
        print(f"  ✅ {path}")
        return True
    elif required:
        print(f"  ❌ THIẾU: {path}")
        return False
    else:
        print(f"  ⚠️  Optional: {path}")
        return True


def check_json(path, required_keys):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        missing = [k for k in required_keys if k not in data]
        if missing:
            print(f"  ❌ {path} thiếu keys: {missing}")
            return False, data
        print(f"  ✅ {path} — keys OK")
        return True, data
    except Exception as e:
        print(f"  ❌ {path} — {e}")
        return False, None


def validate():
    print("🔍 Kiểm tra bài nộp Lab 24: Eval + Guardrail Stack\n")
    errors = 0
    score = 0
    total = 100

    # ═══ RAGAS Evaluation (30%) ═══
    print("📊 RAGAS Evaluation (30%)")
    print("-" * 40)

    # Test set 50+ questions (10 pts)
    if check_file("phase-a/testset_v1.csv"):
        import csv
        try:
            with open("phase-a/testset_v1.csv", encoding="utf-8") as f:
                ts = list(csv.DictReader(f))
            n = len(ts)
            cats = set(item.get("evolution_type", "") for item in ts)
            if n >= 50:
                print(f"  ✅ Test set: {n} questions (≥50), categories: {cats}")
                score += 10
            else:
                print(f"  ⚠️  Test set: {n} questions (<50)")
                score += 5
                errors += 1
        except Exception as e:
            print(f"  ❌ Error reading testset_v1.csv: {e}")
            errors += 1
    else:
        errors += 1

    # 4 metrics computed (10 pts)
    check_file("phase-a/ragas_results.csv")
    if check_file("phase-a/ragas_summary.json"):
        ok, data = check_json("phase-a/ragas_summary.json", ["faithfulness", "answer_relevancy", "context_precision", "context_recall"])
        if ok and data:
            metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
            computed = [m for m in metrics if m in data and data[m] > 0]
            if len(computed) == 4:
                print(f"  ✅ All 4 metrics computed")
                score += 10
            else:
                print(f"  ⚠️  Only {len(computed)}/4 metrics computed")
                score += 5
                errors += 1
    else:
        errors += 1

    # Failure cluster analysis (5 pts)
    check_file("phase-a/failure_analysis.md")
    if check_file("reports/cluster_analysis.json"):
        ok, data = check_json("reports/cluster_analysis.json", ["clusters", "recommendations"])
        if ok:
            score += 5
    else:
        errors += 1

    # CI/CD plan (5 pts)
    if check_file(".github/workflows/eval-gate.yml") or check_file("analysis/ci_cd_plan.md"):
        score += 5
    else:
        errors += 1

    # ═══ LLM-Judge (25%) ═══
    print("\n⚖️  LLM-Judge (25%)")
    print("-" * 40)

    check_file("phase-b/absolute_scores.csv")
    check_file("phase-b/pairwise_results.csv")
    if check_file("reports/judge_report.json"):
        ok, data = check_json("reports/judge_report.json", ["pairwise", "absolute", "cohen_kappa"])
        if ok and data:
            # Pairwise + absolute (10 pts)
            if data.get("pairwise") and data.get("absolute"):
                print(f"  ✅ Pairwise + Absolute scoring present")
                score += 10
            else:
                errors += 1

            # Bias mitigation (5 pts)
            bias = data.get("bias_mitigation", {})
            if bias.get("swap_results_count", 0) > 0:
                print(f"  ✅ Swap-and-average: {bias['swap_results_count']} results, delta={bias.get('avg_bias_delta', 0):.4f}")
                score += 5
            else:
                print(f"  ⚠️  No swap-and-average results")
                errors += 1

            # Cohen κ (10 pts)
            kappa = data.get("cohen_kappa", {})
            if kappa.get("kappa", 0) != 0 or kappa.get("n", 0) > 0:
                print(f"  ✅ Cohen κ = {kappa.get('kappa', 0)} ({kappa.get('agreement', 'N/A')}), n={kappa.get('n', 0)}")
                score += 10
            else:
                print(f"  ⚠️  Cohen κ not computed")
                score += 3
                errors += 1
    else:
        errors += 1

    # Human annotations
    check_file("phase-b/human_labels.csv")

    # ═══ Guardrails (25%) ═══
    print("\n🛡️  Guardrails (25%)")
    print("-" * 40)

    # Presidio PII (5 pts)
    if check_file("phase-c/input_guard.py") or check_file("src/m7_guardrails.py"):
        print(f"  ✅ Guardrails module exists")
        score += 5  # PII
        score += 5  # Topic validator
    else:
        errors += 2

    check_file("phase-c/pii_test_results.csv")
    
    # Guardrail report / Llama Guard (10 pts)
    if check_file("phase-c/adversarial_test_results.csv"):
        import csv
        try:
            with open("phase-c/adversarial_test_results.csv", encoding="utf-8") as f:
                adv = list(csv.DictReader(f))
            correct = sum(1 for r in adv if r.get("correct") == "True")
            acc = correct / max(len(adv), 1)
            print(f"  ✅ Adversarial test: {len(adv)} tests, accuracy={acc:.2%}")
            score += 10
        except Exception as e:
            print(f"  ❌ Error reading adversarial_test_results.csv: {e}")
            errors += 1
    elif check_file("reports/guardrail_report.json"):
        ok, data = check_json("reports/guardrail_report.json", ["total", "blocked", "accuracy"])
        if ok:
            print(f"  ✅ Adversarial test: {data.get('total', 0)} tests, accuracy={data.get('accuracy', 0):.2%}")
            score += 10
    else:
        errors += 1

    # Latency P95 (5 pts)
    if check_file("phase-c/latency_benchmark.csv"):
        import csv
        try:
            with open("phase-c/latency_benchmark.csv", encoding="utf-8") as f:
                lat = list(csv.DictReader(f))
            l1_p95 = next((float(r["P95_ms"]) for r in lat if r["layer"] == "L1"), 0)
            print(f"  ✅ P95 latency (L1): {l1_p95:.1f}ms")
            score += 5
        except Exception as e:
            print(f"  ❌ Error reading latency_benchmark.csv: {e}")
            errors += 1
    elif check_file("reports/latency_report.json"):
        ok, data = check_json("reports/latency_report.json", ["p50_s", "p95_s"])
        if ok:
            print(f"  ✅ P95 latency: {data.get('p95_s', 0):.3f}s")
            score += 5
    else:
        errors += 1

    # ═══ Blueprint (20%) ═══
    print("\n📋 Blueprint (20%)")
    print("-" * 40)

    if check_file("analysis/blueprint.md"):
        with open("analysis/blueprint.md", encoding="utf-8") as f:
            content = f.read()
        checks = {
            "SLO": "SLO" in content or "slo" in content.lower(),
            "Architecture": "architecture" in content.lower() or "kiến trúc" in content.lower() or "mermaid" in content.lower(),
            "Alert": "alert" in content.lower() or "playbook" in content.lower(),
            "Cost": "cost" in content.lower() or "chi phí" in content.lower(),
        }
        for name, found in checks.items():
            if found:
                print(f"  ✅ {name} section found")
                score += 5
            else:
                print(f"  ⚠️  {name} section missing")
                errors += 1
    else:
        errors += 1

    # ═══ Summary ═══
    print(f"\n{'=' * 50}")
    print(f"📊 Score estimate: {score}/{total}")
    if errors == 0:
        print("🚀 Bài lab sẵn sàng để nộp!")
    else:
        print(f"⚠️  Có {errors} items cần xem lại.")
    print("=" * 50)


if __name__ == "__main__":
    validate()
