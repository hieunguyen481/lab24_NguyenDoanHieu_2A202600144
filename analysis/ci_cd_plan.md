# CI/CD Integration Plan — RAG Pipeline Evaluation

## Overview

Tích hợp automated RAGAS evaluation + guardrail testing vào CI/CD pipeline để detect regression sớm.

## GitHub Actions Workflow

```yaml
name: RAG Evaluation CI

on:
  push:
    branches: [main]
    paths: ['src/**', 'test_set.json', 'data/**']
  schedule:
    - cron: '0 2 * * *'  # Nightly 2AM UTC

jobs:
  eval:
    runs-on: ubuntu-latest
    services:
      qdrant:
        image: qdrant/qdrant:latest
        ports: ['6333:6333']

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run RAGAS Evaluation
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: python main_lab24.py --phase A

      - name: Run Guardrail Tests
        run: python main_lab24.py --phase C

      - name: Assert Metrics ≥ SLO
        run: |
          python -c "
          import json
          with open('reports/ragas_report.json') as f:
              r = json.load(f)
          agg = r['aggregate']
          slo = {'faithfulness': 0.85, 'answer_relevancy': 0.80,
                 'context_precision': 0.75, 'context_recall': 0.85}
          for m, threshold in slo.items():
              score = agg.get(m, 0)
              assert score >= threshold, f'{m}={score:.4f} < {threshold}'
              print(f'✓ {m}: {score:.4f} >= {threshold}')
          "

      - name: Upload Reports
        uses: actions/upload-artifact@v4
        with:
          name: eval-reports
          path: reports/
```

## Regression Test Strategy

| Check | Trigger | Threshold | Action |
|-------|---------|-----------|--------|
| RAGAS 4 metrics | Every push to `src/` | Each metric ≥ SLO - 5% | Block merge |
| Guardrail adversarial | Every push | Accuracy ≥ 80% | Block merge |
| P95 latency | Nightly | ≤ 5s | Alert Slack |
| Metric degradation | Nightly vs 7-day avg | Δ > 5% | Alert + auto-issue |

## Alert on Degradation

```python
# In nightly job:
import json

with open('reports/ragas_report.json') as f:
    current = json.load(f)['aggregate']
with open('reports/baseline_scores.json') as f:
    baseline = json.load(f)

for metric in ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']:
    delta = current[metric] - baseline[metric]
    if delta < -0.05:
        print(f"⚠️ ALERT: {metric} degraded by {abs(delta):.4f}")
        # Send Slack/email notification
```

## Nightly Eval Schedule

- **Frequency**: Daily 2AM UTC
- **Test set**: Full 50+ questions
- **Reports**: Auto-committed to `reports/` branch
- **Dashboard**: Track metrics over time in Grafana/simple HTML

## Rollback Criteria

1. Any RAGAS metric drops > 10% from baseline → auto-rollback
2. Guardrail accuracy < 70% → block deployment
3. P95 latency > 10s → alert + investigate
