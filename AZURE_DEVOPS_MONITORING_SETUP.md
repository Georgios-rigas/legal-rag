# Azure DevOps Monitoring Setup Guide

## Overview

This guide shows you how to set up automated evaluation monitoring in Azure DevOps and where to view your metrics.

## Step 1: Create the Monitoring Pipeline

### 1.1 Navigate to Azure DevOps
1. Go to your Azure DevOps project
2. Click **Pipelines** in the left menu
3. Click **New Pipeline** (or **Create Pipeline**)

### 1.2 Configure Pipeline
1. Select **Azure Repos Git**
2. Select your repository
3. Choose **Existing Azure Pipelines YAML file**
4. Select the file: `/azure-pipelines-monitoring.yml`
5. Click **Continue**

### 1.3 Add Pipeline Variables (Secrets)
Before running, you need to add secrets:

1. Click **Variables** button (top right)
2. Add these variables as **secret** (click the lock icon):
   - `PINECONE_API_KEY` - Your Pinecone API key
   - `ANTHROPIC_API_KEY` - Your Anthropic API key
   - `OPENAI_API_KEY` - Your OpenAI API key
3. Click **Save**

### 1.4 Save and Run
1. Click **Save and run**
2. The first run will execute immediately
3. After that, it runs daily at 2 AM UTC

## Step 2: Where to View Metrics

### Option A: View in Azure DevOps Pipeline Artifacts

#### After Each Pipeline Run:

1. **Go to Pipelines** → Select your monitoring pipeline
2. **Click on a completed run** (e.g., "Run #123")
3. **Click "1 published" under Artifacts** (on the right side)
4. **Download** the `evaluation-results` artifact
5. **Open** the JSON file: `monitoring_eval_12345.json`

#### What You'll See in the JSON:

```json
{
  "retrieval_metrics": {
    "avg_precision@5": 0.850,
    "avg_recall@5": 0.720,
    "avg_mrr": 0.782
  },
  "answer_quality_metrics": {
    "avg_citation_accuracy": 0.967
  },
  "performance_metrics": {
    "avg_total_latency": 5.23,
    "p95_total_latency": 7.12
  },
  "cost_metrics": {
    "avg_cost_per_query": 0.0134,
    "total_cost": 0.67
  }
}
```

### Option B: View in Pipeline Logs

1. **Go to Pipelines** → Select monitoring pipeline
2. **Click on a run**
3. **Click "Check quality gates"** step
4. You'll see output like:

```
✅ PASS: Precision@5 = 0.85 (threshold: 0.70)
✅ PASS: Citation Accuracy = 0.97 (threshold: 0.90)
✅ PASS: Avg Latency = 5.2s (threshold: 10.0s)
✅ PASS: Cost per Query = $0.013 (threshold: $0.05)

✅ All quality gates passed!
```

Or if quality degrades:

```
❌ FAIL: Precision@5 = 0.65 (threshold: 0.70)
✅ PASS: Citation Accuracy = 0.97 (threshold: 0.90)
⚠️  Quality gates failed!
```

### Option C: Track Over Time Manually

Download artifacts from multiple runs and compare:

```bash
# Run 1 (Dec 1)
monitoring_eval_12345.json → Precision@5: 0.85

# Run 2 (Dec 2)
monitoring_eval_12346.json → Precision@5: 0.83

# Run 3 (Dec 3)
monitoring_eval_12347.json → Precision@5: 0.78  ⚠️ Degrading!
```

## Step 3: Manual Trigger (Optional)

Want to run evaluation on-demand without waiting for the schedule?

1. Go to **Pipelines**
2. Select **monitoring pipeline**
3. Click **Run pipeline** (top right)
4. Click **Run**

This is useful for:
- Testing after a deployment
- Checking quality after changing prompts/models
- Generating reports for stakeholders

## Step 4: View Summary Dashboard (Azure DevOps)

Azure DevOps doesn't have built-in dashboards for custom metrics, but you can:

### Option 1: Use Azure DevOps Dashboards
1. Go to **Overview** → **Dashboards**
2. Click **New Dashboard**
3. Add widgets:
   - **Build History** - See pass/fail trends
   - **Test Results Trend** - (if you integrate quality gates as tests)

### Option 2: Export to Excel/Google Sheets
1. Download JSON artifacts from multiple runs
2. Parse metrics into spreadsheet
3. Create charts tracking:
   - Precision@5 over time
   - Latency trends
   - Cost per query

### Option 3: Integrate Weights & Biases (Recommended!)

For automated visualization:

1. Sign up at [wandb.ai](https://wandb.ai) (FREE)
2. Add to `evaluate_rag.py`:

```python
import wandb

# At start of evaluation
wandb.init(project="legal-rag-monitoring")

# After aggregating metrics
wandb.log({
    "precision@5": self.results['retrieval_metrics']['avg_precision@5'],
    "citation_accuracy": self.results['answer_quality_metrics']['avg_citation_accuracy'],
    "latency": self.results['performance_metrics']['avg_total_latency'],
    "cost": self.results['cost_metrics']['avg_cost_per_query']
})
```

3. Add `wandb` to `requirements.txt`
4. Add `WANDB_API_KEY` to pipeline variables

Then view beautiful dashboards at wandb.ai with:
- Line charts showing trends over time
- Automatic regression detection
- Comparison across experiments

## Monitoring Schedule Options

### Current: Daily at 2 AM UTC
```yaml
schedules:
- cron: "0 2 * * *"
```

### Every 6 Hours
```yaml
schedules:
- cron: "0 */6 * * *"
```

### Twice Daily (2 AM and 2 PM)
```yaml
schedules:
- cron: "0 2,14 * * *"
```

### Weekly on Monday
```yaml
schedules:
- cron: "0 2 * * 1"
```

## Cost Breakdown

### Running Evaluation Daily:
- 50 queries × $0.013 per query = **$0.65 per run**
- 30 days × $0.65 = **$19.50/month**

### Running Evaluation Weekly:
- 4 runs × $0.65 = **$2.60/month**

### Recommendation:
Start with **weekly** monitoring, upgrade to daily if needed.

## Alerting (Optional)

Want to get notified when quality drops?

### Email Alerts (Azure DevOps Built-in):
1. Go to **Project Settings** → **Notifications**
2. Click **New subscription**
3. Select **Build completes**
4. Configure:
   - Pipeline: Your monitoring pipeline
   - Filter: "When the build status is Partially succeeded" (from continueOnError)
5. Enter your email
6. Save

You'll get emails when quality gates fail!

### Slack Alerts:
Add to pipeline after quality gates check:

```yaml
- script: |
    if [ $? -ne 0 ]; then
      curl -X POST YOUR_SLACK_WEBHOOK_URL \
        -H 'Content-Type: application/json' \
        -d '{"text":"⚠️ RAG Quality Alert: Metrics below threshold!"}'
    fi
  displayName: 'Send Slack alert'
  condition: failed()
```

## Troubleshooting

### Pipeline fails with "No module named 'query_rag'"
- **Fix**: Make sure pipeline runs in project root directory

### Pipeline fails with "Invalid PINECONE_API_KEY"
- **Fix**: Check that secrets are added as pipeline variables (with lock icon)

### Evaluation takes too long (>10 minutes)
- **Fix**: Use `--max-queries 10` instead of full 50 queries:
  ```yaml
  python evaluate_rag.py --max-queries 10 --output monitoring_eval_$(Build.BuildId).json
  ```

### Can't find artifacts
- **Fix**:
  1. Make sure pipeline completed successfully
  2. Look for "1 published" on the run summary page (top right)
  3. Artifacts are kept for 30 days by default

## Interview Talking Points

When discussing monitoring in interviews:

**"How do you monitor models in production?"**

> "I set up automated evaluation that runs daily on a scheduled Azure DevOps pipeline.
> It evaluates 50 curated test queries against our production RAG system and tracks
> 4 categories of metrics: retrieval quality (Precision@5, Recall@5, MRR), answer
> quality (citation accuracy), performance (latency breakdown), and cost per query.
>
> The results are stored as pipeline artifacts that I can download and analyze. I also
> have quality gates that alert me if metrics drop below thresholds - for example, if
> Precision@5 falls below 0.70 or citation accuracy drops below 0.90.
>
> For visualization, I log metrics to Weights & Biases which gives me dashboards
> showing trends over time. This caught a quality regression where Precision@5 dropped
> from 0.85 to 0.65 after an embedding model change."

**"What metrics do you track?"**

> "I track metrics in 4 categories:
>
> 1. **Retrieval Quality**: Precision@5 (what % of top 5 results are relevant),
>    Recall@5 (did we find all relevant cases), and MRR (is the best result first)
>
> 2. **Answer Quality**: Citation accuracy to detect hallucinations
>
> 3. **Performance**: End-to-end latency with breakdown (embedding: 200ms,
>    search: 300ms, LLM: 5s)
>
> 4. **Cost**: Per-query API costs to ensure economic sustainability
>
> All tracked automatically via scheduled pipeline running daily at 2 AM UTC."

## Next Steps

1. ✅ Create monitoring pipeline in Azure DevOps
2. ✅ Add API key secrets as variables
3. ✅ Run first evaluation manually
4. ✅ Download and review first artifact
5. ⏭️ (Optional) Set up Weights & Biases for visualization
6. ⏭️ (Optional) Configure email/Slack alerts
7. ⏭️ (Optional) Create Excel tracking sheet for metrics

---

**Ready to start!** Create the pipeline in Azure DevOps now and run your first evaluation.
