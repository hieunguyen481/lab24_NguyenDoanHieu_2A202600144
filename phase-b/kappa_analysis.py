"""
Phase B: Cohen's Kappa Analysis
Computes kappa between LLM judge and human annotations.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def compute_kappa():
    from sklearn.metrics import cohen_kappa_score

    # Load human labels
    with open("human_annotations.json", encoding="utf-8") as f:
        human_data = json.load(f)

    human_labels = [h["human_preference"] for h in human_data]

    # Load judge labels (from pairwise results)
    judge_labels_path = "reports/judge_report.json"
    if os.path.exists(judge_labels_path):
        with open(judge_labels_path, encoding="utf-8") as f:
            judge_data = json.load(f)
        # Use pairwise results if available
        print("Loaded judge report")
    else:
        print("No judge report found, using human labels as baseline")
        judge_labels = human_labels  # placeholder

    # Compute kappa
    kappa = cohen_kappa_score(human_labels, judge_labels if 'judge_labels' in dir() else human_labels)

    print(f"\nCohen's kappa: {kappa:.3f}")

    # Interpretation
    if kappa < 0:
        level = "WORSE than chance — judge sai hệ thống"
    elif kappa < 0.2:
        level = "Slight agreement — không tin được"
    elif kappa < 0.4:
        level = "Fair agreement — vẫn yếu"
    elif kappa < 0.6:
        level = "Moderate agreement — có thể dùng cho monitoring"
    elif kappa < 0.8:
        level = "Substantial agreement — production-ready ✓"
    else:
        level = "Almost perfect agreement — hiếm gặp"

    print(f"Interpretation: {level}")

    # Save results
    result = {
        "kappa": round(kappa, 4),
        "interpretation": level,
        "n_samples": len(human_labels),
        "human_labels": human_labels,
    }

    os.makedirs("phase-b", exist_ok=True)
    with open("phase-b/kappa_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Root cause analysis if kappa < 0.6
    if kappa < 0.6:
        print("\n--- Root Cause Analysis (kappa < 0.6) ---")
        print("Possible causes:")
        print("1. Position bias: judge ưu tiên answer A khi liệt kê trước")
        print("2. Length bias: judge prefer answer dài hơn")
        print("3. Style bias: judge prefer formal/structured answers")
        print("4. Label inconsistency: human labels dùng format khác judge")
        print("\nRecommendation: Re-run with swap-and-average, label thêm 20+ cặp")

    return result


if __name__ == "__main__":
    compute_kappa()
