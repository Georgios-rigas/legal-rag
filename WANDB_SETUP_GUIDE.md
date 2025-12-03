# Weights & Biases (W&B) Setup Guide - Automated with Azure DevOps

## Overview

This guide shows you how to set up **automated monitoring** where **every commit** triggers evaluation and logs metrics to Weights & Biases.

## What You'll Get

```
Push Code → Azure DevOps Pipeline → Run Evaluation → W&B Dashboard
                                                            ↓
                                                 View metrics at wandb.ai
```

- 📊 **Automatic dashboards** after every evaluation
- 📈 **Track trends** over time (Precision@5, latency, cost)
- 🔄 **Compare experiments** side-by-side
- 💯 **FREE** for personal use

---

## Step 1: Create W&B Account (2 minutes)

### 1.1 Sign Up

1. Go to [https://wandb.ai/site](https://wandb.ai/site)
2. Click **"Sign Up"**
3. Choose **"Sign up with GitHub"** (easiest)
4. Authorize W&B

### 1.2 Get API Key

1. Go to [https://wandb.ai/authorize](https://wandb.ai/authorize)
2. Copy your API key (looks like: `a1b2c3d4e5f6...`)
3. Save it somewhere safe

---

## Step 2: Add W&B API Key to Azure DevOps (3 minutes)

### 2.1 Add Secret Variable

1. Go to **Azure DevOps** → Your project
2. Go to **Pipelines**
3. Select your **monitoring pipeline** (the one we created earlier)
4. Click **Edit**
5. Click **Variables** (top right)
6. Click **New variable**
7. Configure:
   - **Name**: `WANDB_API_KEY`
   - **Value**: Paste your API key from Step 1.2
   - **✅ Keep this value secret** (click the lock icon)
8. Click **OK**
9. Click **Save**

---

## Step 3: Verify Integration (Already Done! ✅)

The code is already updated:

- ✅ `evaluate_rag.py` has W&B logging code
- ✅ `azure-pipelines-monitoring.yml` has W&B environment variables
- ✅ `requirements.txt` includes `wandb`

---

## Step 4: Test It! (5 minutes)

### 4.1 Commit and Push

Your updated files are ready. Let's commit:

```bash
git add evaluate_rag.py azure-pipelines-monitoring.yml requirements.txt
git commit -m "Add Weights & Biases integration for automated monitoring"
git push azuredevops main
```

### 4.2 Run the Monitoring Pipeline

**Option A: Wait for scheduled run** (runs daily at 2 AM)

**Option B: Trigger manually** (do this now to test!):
1. Go to **Azure DevOps** → **Pipelines**
2. Select **monitoring pipeline**
3. Click **Run pipeline**
4. Click **Run**

### 4.3 Watch It Work

In the pipeline logs, you'll see:

```
✅ Weights & Biases integration enabled
📊 W&B Run: https://wandb.ai/your-username/legal-rag-monitoring/runs/abc123

Running evaluation on 50 queries...
...
✅ Metrics logged to Weights & Biases: https://wandb.ai/...
```

Click the URL to see your dashboard!

---

## Step 5: View Your Metrics in W&B

### 5.1 Open W&B Dashboard

1. Go to [https://wandb.ai](https://wandb.ai)
2. Click **Projects** (left sidebar)
3. Click **legal-rag-monitoring**

You'll see a table of all evaluation runs!

### 5.2 View Individual Run

Click on any run to see:

- **Overview**: Summary of all metrics
- **Charts**: Automatic visualizations
- **System**: Hardware/environment info
- **Logs**: Full evaluation logs

### 5.3 Compare Multiple Runs

1. Select 2+ runs (checkboxes on left)
2. Click **"Compare"** button
3. See side-by-side comparison:

```
Run 1 (Dec 3)       vs       Run 2 (Dec 4)
═══════════════════════════════════════════
Precision@5: 0.85           Precision@5: 0.82   ↓ -3.5%
Latency: 5.2s               Latency: 5.5s       ↑ +5.8%
Cost: $0.013                Cost: $0.014        ↑ +7.7%
```

### 5.4 Create Custom Charts

**Track Precision@5 Over Time:**

1. Go to **Workspace** tab
2. Click **"Add Visualization"**
3. Configure:
   - **X-axis**: Step or timestamp
   - **Y-axis**: `precision@5`
   - **Chart type**: Line chart
4. Click **Save**

Pin this chart for easy access!

---

## How It Works After Setup

### Daily Automated Flow:

```
1. ⏰ 2 AM UTC - Azure DevOps pipeline triggers
2. 🏃 Pipeline runs evaluate_rag.py
3. 📊 Evaluation runs 50 test queries
4. ✅ Metrics logged to W&B automatically
5. 📈 Dashboard updates with new data point
6. 📧 (Optional) Get email if quality drops
```

### After Code Changes:

When you push code changes that affect the backend:

```
1. 💻 You push changes to Azure DevOps
2. 🔨 Backend pipeline builds & deploys
3. ⏳ Wait a few hours (or trigger manually)
4. 🏃 Monitoring pipeline runs
5. 📊 New metrics appear in W&B
6. 📈 Compare before/after to see impact
```

---

## What Metrics You'll See

### Retrieval Quality
- **Precision@5**: % of top 5 results that are relevant
- **Recall@5**: % of all relevant cases found
- **MRR**: Mean Reciprocal Rank (position of first relevant result)

### Answer Quality
- **Citation Accuracy**: % of citations that are real (not hallucinated)

### Performance
- **avg_latency**: Average end-to-end query time
- **p95_latency**: 95th percentile latency
- **embedding_time**: Time for OpenAI embedding
- **search_time**: Time for Pinecone search
- **llm_time**: Time for Claude generation

### Cost
- **cost_per_query**: Average API cost per query
- **total_cost**: Total cost for evaluation run

---

## Example Use Cases

### 1. Detect Quality Regressions

**Scenario**: You change the prompt

**Flow**:
1. Deploy new prompt
2. Wait for next evaluation run (or trigger manually)
3. W&B shows: Precision@5 dropped from 0.85 to 0.72 ❌
4. You revert the prompt change
5. Next run shows: Precision@5 back to 0.85 ✅

### 2. Compare Model Versions

**Scenario**: Test OpenAI vs Cohere embeddings

**Flow**:
1. Baseline: Current system with OpenAI
   - W&B Run 1: Precision@5 = 0.85, Cost = $0.013
2. Change config to use Cohere embeddings
3. Deploy and run evaluation
   - W&B Run 2: Precision@5 = 0.80, Cost = $0.009
4. Compare in W&B:
   - Cohere: 6% lower quality, but 31% cheaper
5. Make data-driven decision

### 3. Track Quality Over Time

**Scenario**: Monitor production quality drift

**Flow**:
1. Week 1: Precision@5 = 0.85
2. Week 2: Precision@5 = 0.84
3. Week 3: Precision@5 = 0.82
4. Week 4: Precision@5 = 0.78 ⚠️

**Action**: W&B chart shows downward trend → Investigate why quality is degrading

---

## Interview Talking Points

When discussing monitoring in interviews:

**"How do you monitor your RAG system in production?"**

> "I use Weights & Biases integrated with Azure DevOps for automated monitoring.
> Every day, a scheduled pipeline runs 50 curated test queries through my system
> and logs metrics like Precision@5, citation accuracy, latency, and cost to W&B.
>
> This gives me a historical view of system performance. For example, I can see
> that Precision@5 has been stable at 0.85 for the past month, but last week
> latency spiked from 5.2s to 6.8s, which led me to investigate and discover a
> Pinecone index issue.
>
> I also use W&B for A/B testing. When I tested OpenAI vs Cohere embeddings,
> W&B showed me the quality/cost tradeoff in a clear dashboard, which helped me
> make a data-driven decision."

**"How do you track experiments?"**

> "Every evaluation run is logged to Weights & Biases with full metadata including
> embedding model, LLM version, and prompt version. I can filter runs by any of
> these tags to understand the impact of specific changes.
>
> For example, I can pull up all runs using 'claude-sonnet-4.5' vs 'claude-haiku'
> and W&B automatically generates comparison charts showing that Haiku is 60%
> faster but has 8% lower citation accuracy. This data-driven approach helps me
> make the right tradeoffs."

---

## Cost

**Weights & Biases FREE Tier:**
- ✅ Unlimited runs
- ✅ 100GB storage
- ✅ Team collaboration (up to 2 people)
- ✅ All features enabled
- **Cost**: $0/month

**Azure DevOps Pipeline:**
- Running evaluation: ~$0.65 per run (API costs)
- Daily schedule: ~$20/month
- Weekly schedule: ~$2.60/month

**Recommendation**: Start with weekly schedule to save costs.

---

## Troubleshooting

### Pipeline fails with "wandb.errors.CommError"
- **Fix**: Check that `WANDB_API_KEY` variable is set in Azure DevOps
- Verify the API key is correct at [wandb.ai/authorize](https://wandb.ai/authorize)

### No metrics showing in W&B
- **Fix**: Check pipeline logs for "✅ Metrics logged to Weights & Biases"
- If missing, verify `WANDB_ENABLED: true` is in pipeline YAML

### W&B says "Invalid API key"
- **Fix**: Generate new API key at [wandb.ai/authorize](https://wandb.ai/authorize)
- Update `WANDB_API_KEY` variable in Azure DevOps

### Charts not appearing
- **Fix**: You need at least 2 runs to see trends
- Run pipeline manually 2-3 times to generate initial data

---

## Next Steps

1. ✅ Create W&B account
2. ✅ Add API key to Azure DevOps
3. ✅ Commit updated files
4. ✅ Run pipeline manually to test
5. ✅ View dashboard at wandb.ai
6. ⏭️ (Optional) Set up Slack alerts in W&B
7. ⏭️ (Optional) Create custom dashboards
8. ⏭️ (Optional) Share dashboard with team/interviewers

---

## Advanced: Slack Alerts

Want to get notified in Slack when quality drops?

### Setup (5 minutes):

1. Go to W&B project settings
2. Click **"Alerts"**
3. Click **"New Alert"**
4. Configure:
   - **Metric**: `precision@5`
   - **Condition**: Less than `0.75`
   - **Action**: Send to Slack webhook
5. Add your Slack webhook URL
6. Save

Now you'll get Slack messages when quality drops below threshold!

---

**Ready to go!** Follow the steps above and you'll have automated monitoring running after every commit.

View your metrics at: **[https://wandb.ai](https://wandb.ai)**
