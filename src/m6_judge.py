"""
Module 6: LLM-as-a-Judge — Pairwise, Absolute, Swap-and-Average, Cohen κ.

Lab 24 Phase B: Build LLM judge pipeline for RAG evaluation.
"""

import os, sys, json, re
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import JUDGE_MODEL, JUDGE_CRITERIA, HUMAN_ANNOTATIONS_PATH


@dataclass
class JudgeResult:
    question: str
    verdict: str  # "A", "B", "Tie"
    reasoning: str
    score_a: float
    score_b: float


# ─── Helper: Call LLM ────────────────────────────────────


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """Call OpenAI LLM for judging."""
    try:
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model=JUDGE_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=500,
            temperature=0.0,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"


# ─── 1. Pairwise Evaluation ─────────────────────────────


PAIRWISE_PROMPT = """Bạn là judge chuyên đánh giá chất lượng câu trả lời RAG.
So sánh Answer A và Answer B cho câu hỏi dưới đây.
Chọn answer tốt hơn dựa trên: correctness, completeness, relevance.

Trả về JSON: {"verdict": "A" hoặc "B" hoặc "Tie", "reasoning": "giải thích ngắn"}"""


def pairwise_judge(question: str, answer_a: str, answer_b: str,
                   ground_truth: str = "") -> JudgeResult:
    """Compare two answers, return which is better."""
    user_msg = f"""Question: {question}
Ground Truth: {ground_truth}

Answer A: {answer_a}

Answer B: {answer_b}"""

    raw = _call_llm(PAIRWISE_PROMPT, user_msg)
    try:
        data = json.loads(raw)
        verdict = data.get("verdict", "Tie")
        reasoning = data.get("reasoning", "")
    except (json.JSONDecodeError, Exception):
        verdict = "Tie"
        reasoning = raw

    return JudgeResult(
        question=question, verdict=verdict, reasoning=reasoning,
        score_a=1.0 if verdict == "A" else (0.5 if verdict == "Tie" else 0.0),
        score_b=1.0 if verdict == "B" else (0.5 if verdict == "Tie" else 0.0),
    )


# ─── 2. Absolute Scoring ────────────────────────────────


ABSOLUTE_PROMPT = """Bạn là judge đánh giá chất lượng câu trả lời RAG.
Cho điểm answer trên thang 1-5 cho mỗi tiêu chí:
- correctness: Thông tin có chính xác không?
- completeness: Câu trả lời có đầy đủ không?
- relevance: Có liên quan đến câu hỏi không?
- coherence: Văn phong có mạch lạc không?

Trả về JSON: {"correctness": X, "completeness": X, "relevance": X, "coherence": X, "overall": X}
Trong đó X là số từ 1-5."""


def absolute_judge(question: str, answer: str,
                   ground_truth: str = "") -> dict:
    """Score a single answer on 1-5 scale across criteria."""
    user_msg = f"""Question: {question}
Ground Truth: {ground_truth}

Answer: {answer}"""

    raw = _call_llm(ABSOLUTE_PROMPT, user_msg)
    try:
        scores = json.loads(raw)
        for c in JUDGE_CRITERIA + ["overall"]:
            scores.setdefault(c, 3)
        return scores
    except (json.JSONDecodeError, Exception):
        return {c: 3 for c in JUDGE_CRITERIA + ["overall"]}


# ─── 3. Swap-and-Average (Bias Mitigation) ──────────────


def swap_and_average(question: str, answer_a: str, answer_b: str,
                     ground_truth: str = "") -> dict:
    """Run pairwise twice with swapped order, average results."""
    # Round 1: A first
    r1 = pairwise_judge(question, answer_a, answer_b, ground_truth)
    # Round 2: B first (swapped)
    r2 = pairwise_judge(question, answer_b, answer_a, ground_truth)

    # Map r2 back: if r2 says "A" it means original "B"
    r2_mapped_verdict = "B" if r2.verdict == "A" else ("A" if r2.verdict == "B" else "Tie")

    # Compute final scores
    s_a = (r1.score_a + (1.0 - r2.score_a)) / 2
    s_b = (r1.score_b + (1.0 - r2.score_b)) / 2

    if abs(s_a - s_b) < 0.1:
        final_verdict = "Tie"
    else:
        final_verdict = "A" if s_a > s_b else "B"

    bias_delta = abs(r1.score_a - (1.0 - r2.score_a))

    return {
        "question": question,
        "round1_verdict": r1.verdict,
        "round2_verdict": r2_mapped_verdict,
        "final_verdict": final_verdict,
        "score_a": s_a,
        "score_b": s_b,
        "bias_delta": bias_delta,
        "reasoning_r1": r1.reasoning,
        "reasoning_r2": r2.reasoning,
    }


# ─── 4. Cohen's Kappa ───────────────────────────────────


def compute_cohen_kappa(llm_labels: list[str],
                        human_labels: list[str]) -> dict:
    """Compute Cohen's kappa between LLM judge and human annotations."""
    try:
        from sklearn.metrics import cohen_kappa_score
        kappa = cohen_kappa_score(human_labels, llm_labels)
    except ImportError:
        # Manual computation
        n = len(llm_labels)
        if n == 0:
            return {"kappa": 0.0, "agreement": "none", "n": 0}
        agree = sum(1 for a, b in zip(llm_labels, human_labels) if a == b)
        po = agree / n
        labels = list(set(llm_labels + human_labels))
        pe = sum(
            (llm_labels.count(l) / n) * (human_labels.count(l) / n)
            for l in labels
        )
        kappa = (po - pe) / (1 - pe) if pe < 1 else 0.0

    # Interpret kappa
    if kappa < 0.0:
        level = "poor"
    elif kappa < 0.20:
        level = "slight"
    elif kappa < 0.40:
        level = "fair"
    elif kappa < 0.60:
        level = "moderate"
    elif kappa < 0.80:
        level = "substantial"
    else:
        level = "almost_perfect"

    return {
        "kappa": round(kappa, 4),
        "agreement": level,
        "n": len(llm_labels),
        "accuracy": round(sum(1 for a, b in zip(llm_labels, human_labels) if a == b) / max(len(llm_labels), 1), 4),
    }


# ─── 5. Full Judge Pipeline ─────────────────────────────


def run_judge_pipeline(test_items: list[dict],
                       answers_a: list[str],
                       answers_b: list[str]) -> dict:
    """
    Run complete LLM-Judge pipeline.

    Args:
        test_items: List of {"question": ..., "ground_truth": ...}
        answers_a: Naive baseline answers
        answers_b: Production pipeline answers

    Returns:
        Full judge report dict.
    """
    pairwise_results = []
    swap_results = []
    absolute_a_scores = []
    absolute_b_scores = []

    for i, item in enumerate(test_items[:30]): # Ensure we run on at least 30 questions
        q = item["question"]
        gt = item.get("ground_truth", "")
        a_a = answers_a[i] if i < len(answers_a) else ""
        a_b = answers_b[i] if i < len(answers_b) else ""

        print(f"  [Judge {i+1}/{min(len(test_items), 30)}] {q[:50]}...")

        # Pairwise
        pr = pairwise_judge(q, a_a, a_b, gt)
        pairwise_results.append(pr)

        # Swap-and-average
        sr = swap_and_average(q, a_a, a_b, gt)
        swap_results.append(sr)

        # Absolute scoring
        abs_a = absolute_judge(q, a_a, gt)
        abs_a["question"] = q
        abs_a["model"] = "baseline"
        
        abs_b = absolute_judge(q, a_b, gt)
        abs_b["question"] = q
        abs_b["model"] = "production"
        
        absolute_a_scores.append(abs_a)
        absolute_b_scores.append(abs_b)

    # Export absolute scores
    import csv
    os.makedirs("phase-b", exist_ok=True)
    with open("phase-b/absolute_scores.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = ["question", "model"] + JUDGE_CRITERIA + ["overall"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for a_score, b_score in zip(absolute_a_scores, absolute_b_scores):
            writer.writerow(a_score)
            writer.writerow(b_score)

    # Export pairwise results
    with open("phase-b/pairwise_results.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = ["question", "winner_after_swap", "run1_winner", "run2_winner"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for sr in swap_results:
            writer.writerow({
                "question": sr["question"],
                "winner_after_swap": sr["final_verdict"],
                "run1_winner": sr["round1_verdict"],
                "run2_winner": sr["round2_verdict"]
            })

    # Aggregate pairwise
    a_wins = sum(1 for r in pairwise_results if r.verdict == "A")
    b_wins = sum(1 for r in pairwise_results if r.verdict == "B")
    ties = sum(1 for r in pairwise_results if r.verdict == "Tie")

    # Aggregate absolute
    def avg_scores(scores_list):
        if not scores_list:
            return {}
        result = {}
        for key in JUDGE_CRITERIA + ["overall"]:
            vals = [s.get(key, 3) for s in scores_list]
            result[key] = round(sum(vals) / len(vals), 2)
        return result

    # Aggregate bias
    avg_bias = 0.0
    if swap_results:
        avg_bias = sum(r["bias_delta"] for r in swap_results) / len(swap_results)

    # Cohen kappa with human annotations
    kappa_result = {"kappa": 0.0, "agreement": "not_computed", "n": 0}
    try:
        human_labels_csv = "phase-b/human_labels.csv"
        if os.path.exists(human_labels_csv):
            with open(human_labels_csv, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                human_data = list(reader)
            if human_data and human_data[0].get("human_winner"):
                human_labels = [h["human_winner"].upper() for h in human_data]
                # Match LLM labels for same questions (assuming sequential for first 10)
                llm_labels = [r["final_verdict"] for r in swap_results[:len(human_labels)]]
                kappa_result = compute_cohen_kappa(llm_labels, human_labels)
    except Exception as e:
        kappa_result["error"] = str(e)

    report = {
        "pairwise": {
            "a_wins": a_wins,
            "b_wins": b_wins,
            "ties": ties,
            "total": len(pairwise_results),
            "b_win_rate": round(b_wins / max(len(pairwise_results), 1), 4),
        },
        "absolute": {
            "baseline_avg": avg_scores(absolute_a_scores),
            "production_avg": avg_scores(absolute_b_scores),
        },
        "bias_mitigation": {
            "avg_bias_delta": round(avg_bias, 4),
            "swap_results_count": len(swap_results),
        },
        "cohen_kappa": kappa_result,
    }

    # Save report
    os.makedirs("reports", exist_ok=True)
    with open("reports/judge_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  Judge report saved to reports/judge_report.json")

    return report


if __name__ == "__main__":
    print("=== LLM Judge Module ===")
    print("Use run_judge_pipeline() from main_lab24.py")
