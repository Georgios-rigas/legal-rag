# CI/CD Integration and Model Monitoring Guide

This guide explains how to integrate model evaluation into your CI/CD pipeline and set up production monitoring for your Legal RAG system.

## Table of Contents
1. [CI/CD Integration](#cicd-integration)
2. [Model Monitoring Setup](#model-monitoring-setup)
3. [Recommended Tools](#recommended-tools)
4. [Implementation Steps](#implementation-steps)

---

## CI/CD Integration

### Overview

Integrate evaluation into your pipeline to ensure code changes don't degrade model quality.

### Pipeline Flow

```
Git Push → Build → Evaluate Model → Quality Gates → Deploy (if passed)
```

### Azure DevOps Pipeline Configuration

Create `azure-pipelines-evaluation.yml`:

```yaml
trigger:
  branches:
    include:
    - main
  paths:
    include:
    - api.py
    - query_rag.py
    - config.py
    - requirements.txt
    - evaluation_dataset.json

variables:
  pythonVersion: '3.11'

pool:
  vmImage: 'ubuntu-latest'

stages:
- stage: EvaluateModel
  displayName: 'Evaluate RAG Model'
  jobs:
  - job: RunEvaluation
    displayName: 'Run Model Evaluation'
    timeoutInMinutes: 30

    steps:
    - task: UsePythonVersion@0
      displayName: 'Set Python Version'
      inputs:
        versionSpec: '$(pythonVersion)'

    - script: |
        pip install --upgrade pip
        pip install -r requirements.txt
      displayName: 'Install Dependencies'

    # Get secrets from Azure Key Vault (recommended) or Pipeline Variables
    - task: AzureKeyVault@2
      displayName: 'Get API Keys from Key Vault'
      inputs:
        azureSubscription: 'Azure-Personal-SC'
        KeyVaultName: 'legal-rag-kv'  # Create this in Azure
        SecretsFilter: '*'

    - script: |
        # Run evaluation on subset (10 queries for speed)
        python evaluate_rag.py \
          --dataset evaluation_dataset.json \
          --output evaluation_results_$(Build.BuildId).json \
          --max-queries 10
      displayName: 'Run Model Evaluation'
      env:
        PINECONE_API_KEY: $(PINECONE-API-KEY)
        ANTHROPIC_API_KEY: $(ANTHROPIC-API-KEY)
        OPENAI_API_KEY: $(OPENAI-API-KEY)
        AWS_ACCESS_KEY_ID: $(AWS-ACCESS-KEY-ID)
        AWS_SECRET_ACCESS_KEY: $(AWS-SECRET-ACCESS-KEY)
        EMBEDDING_PROVIDER: openai
        LLM_PROVIDER: claude

    - task: PublishBuildArtifacts@1
      displayName: 'Publish Evaluation Results'
      inputs:
        PathtoPublish: 'evaluation_results_$(Build.BuildId).json'
        ArtifactName: 'evaluation-results'

    - script: |
        # Quality Gates Script
        python scripts/check_quality_gates.py \
          evaluation_results_$(Build.BuildId).json
      displayName: 'Check Quality Gates'
      continueOnError: false  # Fail pipeline if gates not met

- stage: Deploy
  displayName: 'Deploy to AKS'
  dependsOn: EvaluateModel
  condition: succeeded()  # Only deploy if evaluation passed
  jobs:
  - deployment: DeployToAKS
    environment: 'production'
    strategy:
      runOnce:
        deploy:
          steps:
          - script: echo "Deploying to AKS..."
            displayName: 'Deploy'
          # Include your existing deployment steps here
```

### Quality Gates Script

Create `scripts/check_quality_gates.py`:

```python
"""
Quality Gates Checker
Fails CI/CD pipeline if metrics below thresholds
"""
import json
import sys

def check_quality_gates(results_file):
    """Check if evaluation results meet quality thresholds."""

    with open(results_file) as f:
        results = json.load(f)

    # Define thresholds (minimum requirements)
    THRESHOLDS = {
        'precision@5': 0.70,       # 70% precision minimum
        'citation_accuracy': 0.90,  # 90% citation accuracy minimum
        'avg_latency': 10.0,        # 10 seconds maximum latency
        'p95_latency': 15.0,        # 15 seconds p95 latency
        'cost_per_query': 0.05      # $0.05 maximum cost per query
    }

    failures = []

    # Check retrieval quality
    if results.get('retrieval_metrics'):
        precision = results['retrieval_metrics'].get('avg_precision@5', 0)
        if precision < THRESHOLDS['precision@5']:
            failures.append(
                f"❌ Precision@5 ({precision:.3f}) below threshold "
                f"({THRESHOLDS['precision@5']})"
            )

    # Check answer quality
    if results.get('answer_quality_metrics'):
        citation_acc = results['answer_quality_metrics'].get('avg_citation_accuracy', 0)
        if citation_acc < THRESHOLDS['citation_accuracy']:
            failures.append(
                f"❌ Citation accuracy ({citation_acc:.3f}) below threshold "
                f"({THRESHOLDS['citation_accuracy']})"
            )

    # Check performance
    if results.get('performance_metrics'):
        avg_latency = results['performance_metrics'].get('avg_total_latency', 0)
        p95_latency = results['performance_metrics'].get('p95_total_latency', 0)

        if avg_latency > THRESHOLDS['avg_latency']:
            failures.append(
                f"❌ Average latency ({avg_latency:.2f}s) above threshold "
                f"({THRESHOLDS['avg_latency']}s)"
            )

        if p95_latency > THRESHOLDS['p95_latency']:
            failures.append(
                f"❌ P95 latency ({p95_latency:.2f}s) above threshold "
                f"({THRESHOLDS['p95_latency']}s)"
            )

    # Check cost
    if results.get('cost_metrics'):
        cost = results['cost_metrics'].get('avg_cost_per_query', 0)
        if cost > THRESHOLDS['cost_per_query']:
            failures.append(
                f"❌ Cost per query (${cost:.4f}) above threshold "
                f"(${THRESHOLDS['cost_per_query']})"
            )

    # Print results
    print("=" * 80)
    print("QUALITY GATE RESULTS")
    print("=" * 80)

    if failures:
        print("\n❌ FAILED - Quality gates not met:\n")
        for failure in failures:
            print(f"  {failure}")
        print("\n" + "=" * 80)
        sys.exit(1)  # Fail the pipeline
    else:
        print("\n✅ PASSED - All quality gates met!\n")
        print(f"  ✓ Precision@5: {results.get('retrieval_metrics', {}).get('avg_precision@5', 0):.3f}")
        print(f"  ✓ Citation Accuracy: {results.get('answer_quality_metrics', {}).get('avg_citation_accuracy', 0):.3f}")
        print(f"  ✓ Avg Latency: {results.get('performance_metrics', {}).get('avg_total_latency', 0):.2f}s")
        print(f"  ✓ Cost/Query: ${results.get('cost_metrics', {}).get('avg_cost_per_query', 0):.4f}")
        print("\n" + "=" * 80)
        sys.exit(0)  # Pass the pipeline

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_quality_gates.py <results_file>")
        sys.exit(1)

    check_quality_gates(sys.argv[1])
```

### GitHub Actions Alternative

If using GitHub Actions instead of Azure DevOps, create `.github/workflows/evaluate-model.yml`:

```yaml
name: Model Evaluation

on:
  push:
    branches: [main]
    paths:
      - 'api.py'
      - 'query_rag.py'
      - 'config.py'
      - 'requirements.txt'
      - 'evaluation_dataset.json'
  pull_request:
    branches: [main]

jobs:
  evaluate:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run evaluation
      env:
        PINECONE_API_KEY: ${{ secrets.PINECONE_API_KEY }}
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        EMBEDDING_PROVIDER: openai
        LLM_PROVIDER: claude
      run: |
        python evaluate_rag.py --max-queries 10 --output results.json

    - name: Check quality gates
      run: |
        python scripts/check_quality_gates.py results.json

    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: evaluation-results
        path: results.json
```

---

## Model Monitoring Setup

### Recommended Tools

For production ML monitoring, I recommend **3-tier monitoring**:

#### 1. **Application Performance Monitoring (APM)**
**Recommended: Azure Application Insights** (Already integrated with Azure)

**Why Application Insights?**
- Native Azure integration
- Real-time metrics tracking
- Automatic anomaly detection
- Cost-effective (~$2-10/month)
- Built-in dashboards

**Alternative: Datadog** (More features, more expensive ~$15-50/month)

#### 2. **ML-Specific Monitoring**
**Recommended: Weights & Biases (W&B)** or **MLflow**

**Weights & Biases:**
- Free tier available
- Excellent for experiment tracking
- Great visualizations
- Easy to integrate

**MLflow:**
- Open source (free)
- Self-hosted option
- Model registry
- Experiment tracking

#### 3. **Custom Metrics Dashboard**
**Recommended: Grafana** (for visualizations)

**Why Grafana?**
- Open source
- Beautiful dashboards
- Connects to multiple data sources
- Industry standard

---

## Implementation Steps

### Step 1: Set Up Azure Application Insights

```python
# File: monitoring.py
"""
Application Insights integration for production monitoring
"""
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure import metrics_exporter
import logging
import time

class RAGMonitoring:
    """Monitor RAG system performance in production."""

    def __init__(self, instrumentation_key: str):
        """Initialize Application Insights."""
        # Set up logger
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(
            AzureLogHandler(connection_string=f'InstrumentationKey={instrumentation_key}')
        )

        # Set up metrics exporter
        self.metrics_exporter = metrics_exporter.new_metrics_exporter(
            connection_string=f'InstrumentationKey={instrumentation_key}'
        )

    def track_query(
        self,
        query: str,
        precision: float,
        latency: float,
        cost: float,
        citations_valid: bool
    ):
        """Track a single query's metrics."""

        # Log event
        self.logger.info(
            "RAG Query",
            extra={
                'custom_dimensions': {
                    'query_length': len(query),
                    'precision': precision,
                    'latency': latency,
                    'cost': cost,
                    'citations_valid': citations_valid,
                    'timestamp': time.time()
                }
            }
        )

        # Send custom metrics
        # These will appear in Application Insights metrics explorer
        self.metrics_exporter.emit({
            'name': 'RAG_Precision',
            'value': precision
        })

        self.metrics_exporter.emit({
            'name': 'RAG_Latency',
            'value': latency
        })

        self.metrics_exporter.emit({
            'name': 'RAG_Cost',
            'value': cost
        })
```

**Update api.py to use monitoring:**

```python
# In api.py

from monitoring import RAGMonitoring
import os

# Initialize monitoring
monitoring = RAGMonitoring(
    instrumentation_key=os.getenv('APPINSIGHTS_INSTRUMENTATION_KEY')
)

@app.post("/api/query")
async def query(request: QueryRequest):
    start_time = time.time()

    # ... existing code ...

    # Track metrics
    latency = time.time() - start_time

    monitoring.track_query(
        query=request.query,
        precision=0.85,  # Calculate actual precision if ground truth available
        latency=latency,
        cost=0.013,  # Calculate actual cost
        citations_valid=True  # Verify citations
    )

    return response
```

### Step 2: Set Up Weights & Biases for Experiment Tracking

```python
# File: wandb_tracking.py
"""
Weights & Biases integration for experiment tracking
"""
import wandb
import json

def log_evaluation_to_wandb(results_file: str, config: dict):
    """Log evaluation results to W&B."""

    # Initialize W&B run
    wandb.init(
        project="legal-rag",
        config=config,
        tags=["evaluation", config.get("embedding_model", "openai")]
    )

    # Load results
    with open(results_file) as f:
        results = json.load(f)

    # Log metrics
    wandb.log({
        "precision@5": results['retrieval_metrics']['avg_precision@5'],
        "recall@5": results['retrieval_metrics']['avg_recall@5'],
        "mrr": results['retrieval_metrics']['avg_mrr'],
        "citation_accuracy": results['answer_quality_metrics']['avg_citation_accuracy'],
        "avg_latency": results['performance_metrics']['avg_total_latency'],
        "p95_latency": results['performance_metrics']['p95_total_latency'],
        "avg_cost": results['cost_metrics']['avg_cost_per_query']
    })

    # Log per-query results as table
    per_query_table = wandb.Table(
        columns=["query_id", "category", "precision", "latency", "cost"],
        data=[
            [
                r["query_id"],
                r["category"],
                r["retrieval_metrics"].get("precision@5", 0),
                r["performance_metrics"]["total_latency"],
                r["cost_metrics"]["total_cost"]
            ]
            for r in results["per_query_results"]
        ]
    )

    wandb.log({"per_query_results": per_query_table})

    # Finish run
    wandb.finish()

# Usage in evaluate_rag.py:
if __name__ == "__main__":
    evaluator = RAGEvaluator()
    results = evaluator.run_evaluation()
    evaluator.save_results("results.json")

    # Log to W&B
    log_evaluation_to_wandb(
        "results.json",
        config={
            "embedding_model": "openai",
            "llm_model": "claude-sonnet-4-5",
            "num_queries": 50
        }
    )
```

### Step 3: Create Grafana Dashboard

**Install Prometheus + Grafana** (can run in Docker on your machine or in AKS):

```yaml
# docker-compose.yml for local monitoring
version: '3'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana

volumes:
  grafana-storage:
```

**Expose metrics from your API:**

```python
# File: metrics.py
"""
Prometheus metrics for RAG API
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Define metrics
query_count = Counter('rag_queries_total', 'Total number of queries')
query_latency = Histogram('rag_query_latency_seconds', 'Query latency')
query_cost = Histogram('rag_query_cost_dollars', 'Query cost')
precision_gauge = Gauge('rag_precision_at_5', 'Current Precision@5')
citation_accuracy = Gauge('rag_citation_accuracy', 'Citation accuracy')

# In api.py
from metrics import query_count, query_latency, query_cost

@app.post("/api/query")
async def query(request: QueryRequest):
    query_count.inc()  # Increment query counter

    with query_latency.time():  # Track latency
        # ... process query ...
        result = rag.query(request.query)

    query_cost.observe(0.013)  # Track cost

    return result

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type="text/plain")
```

**Grafana Dashboard JSON** (import this into Grafana):

```json
{
  "dashboard": {
    "title": "Legal RAG Monitoring",
    "panels": [
      {
        "title": "Queries per Minute",
        "targets": [
          {
            "expr": "rate(rag_queries_total[1m])"
          }
        ]
      },
      {
        "title": "Average Latency",
        "targets": [
          {
            "expr": "rate(rag_query_latency_seconds_sum[5m]) / rate(rag_query_latency_seconds_count[5m])"
          }
        ]
      },
      {
        "title": "P95 Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rag_query_latency_seconds_bucket)"
          }
        ]
      },
      {
        "title": "Cost per Hour",
        "targets": [
          {
            "expr": "sum(rate(rag_query_cost_dollars_sum[1h]))"
          }
        ]
      },
      {
        "title": "Precision@5 (Daily)",
        "targets": [
          {
            "expr": "rag_precision_at_5"
          }
        ]
      }
    ]
  }
}
```

---

## Complete Monitoring Architecture

```
Production System:
  Frontend → Backend API → Pinecone/Claude/OpenAI
                ↓
         [Monitoring Layer]
                ↓
    ┌───────────┼───────────┐
    ↓           ↓           ↓
Application  Prometheus  Weights &
Insights                 Biases
    ↓           ↓
   Azure      Grafana
  Dashboard  Dashboard
```

### What Each Tool Monitors:

**Application Insights:**
- Request/response logs
- Error tracking
- Performance traces
- Custom metrics (precision, cost)
- Automatic alerts

**Prometheus + Grafana:**
- Real-time metrics
- Query rate, latency, cost
- Custom dashboards
- Historical trends

**Weights & Biases:**
- Offline evaluation results
- Experiment comparisons
- Model performance over time
- Per-query analysis

---

## Alerting Setup

### Application Insights Alerts

```bash
# Create alert rule via Azure CLI
az monitor metrics alert create \
  --name "RAG High Latency" \
  --resource-group legal-rag-personal-rg \
  --scopes /subscriptions/.../components/legal-rag-insights \
  --condition "avg RAG_Latency > 10" \
  --window-size 5m \
  --action-groups email-alerts
```

### Slack Notifications

```python
# File: alerts.py
"""
Send alerts to Slack when metrics degrade
"""
import requests
import os

def send_slack_alert(metric_name: str, value: float, threshold: float):
    """Send Slack alert when metric crosses threshold."""

    webhook_url = os.getenv('SLACK_WEBHOOK_URL')

    message = {
        "text": f"🚨 Alert: {metric_name} Threshold Exceeded",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{metric_name}* has exceeded threshold!\n\n"
                            f"Current Value: `{value:.3f}`\n"
                            f"Threshold: `{threshold:.3f}`"
                }
            }
        ]
    }

    requests.post(webhook_url, json=message)
```

---

## Daily/Weekly Evaluation Jobs

### Azure DevOps Scheduled Pipeline

```yaml
# azure-pipelines-scheduled-eval.yml

schedules:
- cron: "0 2 * * *"  # Run at 2 AM daily
  displayName: Daily evaluation
  branches:
    include:
    - main

trigger: none  # Only run on schedule

jobs:
- job: DailyEvaluation
  steps:
  - script: |
      python evaluate_rag.py --output daily_eval_$(date +%Y%m%d).json
    displayName: 'Run Daily Evaluation'

  - script: |
      python scripts/compare_with_baseline.py \
        daily_eval_$(date +%Y%m%d).json \
        baseline_results.json
    displayName: 'Compare with Baseline'
```

---

## Cost and Tool Recommendations

### Budget-Friendly Stack (Free/Cheap):
✅ **Application Insights** - $2-5/month (Azure native)
✅ **W&B Free Tier** - Free for personal projects
✅ **Grafana Open Source** - Free (self-hosted)
✅ **GitHub Actions** - Free for public repos, 2000 min/month private
**Total: ~$5/month**

### Professional Stack ($50-100/month):
✅ **Application Insights** - $10-20/month
✅ **W&B Team Plan** - $50/month
✅ **Datadog** - $15-31/month
✅ **Azure DevOps** - Free tier sufficient
**Total: ~$75-100/month**

### Enterprise Stack ($500+/month):
✅ **Datadog Enterprise** - $200+/month
✅ **W&B Teams** - $50-200/month
✅ **Sentry** - $26+/month
✅ **PagerDuty** - $21+/month
**Total: $300-500/month**

---

## For Interviews - Key Talking Points

**"How do you monitor ML models in production?"**

"I use a 3-tier monitoring approach:

1. **Application Insights** tracks request metrics, latency, and errors in real-time
2. **Weights & Biases** for offline evaluation tracking - I run nightly evaluations on my curated test set and log results to W&B to track Precision@5 trends
3. **Grafana dashboards** visualize Prometheus metrics like query rate, latency distribution, and hourly costs

I also have **quality gates in CI/CD** - before any code deploys, it must pass automated evaluation with Precision@5 > 0.70, latency < 10s, and cost < $0.05/query."

**"How do you detect model degradation?"**

"I run automated evaluation daily on a fixed test set. I compare:
- Current Precision@5 vs 7-day average - alert if drops >5%
- Current citation accuracy vs baseline - alert if <0.90
- Latency P95 - alert if >15 seconds

I also log all production queries and randomly sample 10/day for manual review."

---

## Next Steps

1. ✅ **Create Azure Key Vault** for secrets in CI/CD
2. ✅ **Add evaluation pipeline** to Azure DevOps
3. ✅ **Set up Application Insights** for production monitoring
4. ✅ **Create W&B account** and integrate evaluation logging
5. ✅ **Set up Grafana** (optional, for advanced dashboards)
6. ✅ **Configure Slack alerts** for quality degradation

Start with Application Insights + W&B - that gives you 80% of the value for minimal cost!
