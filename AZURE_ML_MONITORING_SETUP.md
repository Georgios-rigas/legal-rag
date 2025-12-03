# Azure Machine Learning - Production Monitoring & Experimentation

## Overview

For **production monitoring AND experimentation**, you should use **Azure Machine Learning workspace**. This is Microsoft's managed MLOps platform that gives you:

1. **Experiment Tracking** - Track evaluation runs, compare models, visualize metrics
2. **Model Registry** - Version control for your RAG system
3. **Monitoring Dashboards** - Real-time metrics visualization
4. **Data Drift Detection** - Detect when input queries change over time
5. **Cost Tracking** - Monitor Azure costs per experiment
6. **Integration with Azure DevOps** - Auto-log from your pipelines

## Step-by-Step Setup

### Step 1: Create Azure ML Workspace (5 minutes)

#### Option A: Via Azure Portal (Easiest)

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **"Create a resource"**
3. Search for **"Machine Learning"**
4. Click **Create**
5. Configure:
   - **Resource Group**: `legal-rag-personal-rg` (your existing one)
   - **Workspace name**: `legal-rag-ml-workspace`
   - **Region**: `East US` (same as your other resources)
   - **Storage account**: Create new (auto-generated)
   - **Key vault**: Create new (auto-generated)
   - **Application insights**: Create new (auto-generated)
   - **Container registry**: None (optional, you already have ACR)
6. Click **Review + Create**
7. Click **Create**
8. Wait 2-3 minutes for deployment

**Cost**: ~$10-20/month for basic usage (first month often free with credits)

#### Option B: Via Azure CLI

```powershell
az ml workspace create `
  --name legal-rag-ml-workspace `
  --resource-group legal-rag-personal-rg `
  --location eastus
```

### Step 2: Install Azure ML SDK (2 minutes)

Add to your `requirements.txt`:

```
azureml-core
azureml-mlflow
```

Or install now:

```bash
pip install azureml-core azureml-mlflow
```

### Step 3: Configure Logging in evaluate_rag.py (10 minutes)

Update your evaluation script to log to Azure ML:

```python
# Add at top of evaluate_rag.py
from azureml.core import Workspace, Experiment, Run
import os

class RAGEvaluator:
    def __init__(self, dataset_path: str = "evaluation_dataset.json"):
        # ... existing code ...

        # Initialize Azure ML tracking
        self.use_azure_ml = os.getenv("AZURE_ML_TRACKING", "false").lower() == "true"
        if self.use_azure_ml:
            self.ws = Workspace.from_config()  # Reads config.json
            self.experiment = Experiment(workspace=self.ws, name="legal-rag-evaluation")
            self.run = self.experiment.start_logging()
            print(f"Azure ML tracking enabled. Experiment: {self.experiment.name}")

    def run_evaluation(self, max_queries: int = None) -> Dict[str, Any]:
        # ... existing evaluation code ...

        # After aggregating metrics, log to Azure ML
        if self.use_azure_ml and hasattr(self, 'run'):
            self._log_to_azure_ml()

        return self.results

    def _log_to_azure_ml(self):
        """Log metrics to Azure ML workspace."""
        if not hasattr(self, 'run'):
            return

        # Log retrieval metrics
        if self.results["retrieval_metrics"]:
            self.run.log("precision@5", self.results["retrieval_metrics"]["avg_precision@5"])
            self.run.log("recall@5", self.results["retrieval_metrics"]["avg_recall@5"])
            self.run.log("mrr", self.results["retrieval_metrics"]["avg_mrr"])

        # Log answer quality
        if self.results["answer_quality_metrics"]:
            self.run.log("citation_accuracy", self.results["answer_quality_metrics"]["avg_citation_accuracy"])

        # Log performance
        if self.results["performance_metrics"]:
            self.run.log("avg_latency", self.results["performance_metrics"]["avg_total_latency"])
            self.run.log("p95_latency", self.results["performance_metrics"]["p95_total_latency"])
            self.run.log("embedding_time", self.results["performance_metrics"]["avg_embedding_time"])
            self.run.log("search_time", self.results["performance_metrics"]["avg_search_time"])
            self.run.log("llm_time", self.results["performance_metrics"]["avg_llm_time"])

        # Log cost
        if self.results["cost_metrics"]:
            self.run.log("cost_per_query", self.results["cost_metrics"]["avg_cost_per_query"])
            self.run.log("total_cost", self.results["cost_metrics"]["total_cost"])

        # Log metadata
        self.run.log("num_queries", len(self.results["per_query_results"]))
        self.run.log("embedding_provider", "openai")
        self.run.log("llm_provider", "claude")

        print("✅ Metrics logged to Azure ML")

        # Complete the run
        self.run.complete()

    def save_results(self, output_path: str = "evaluation_results.json"):
        # ... existing save code ...

        # Upload results file to Azure ML
        if self.use_azure_ml and hasattr(self, 'run'):
            self.run.upload_file(name="evaluation_results.json", path_or_stream=output_path)
            print(f"✅ Results uploaded to Azure ML")
```

### Step 4: Create Azure ML Config File

Download workspace config:

1. Go to [Azure ML Studio](https://ml.azure.com)
2. Select your workspace: `legal-rag-ml-workspace`
3. Click workspace name (top left) → **Download config.json**
4. Save it to your project root: `config.json`

**IMPORTANT**: Add to `.gitignore`:
```
config.json
```

The config.json looks like:
```json
{
    "subscription_id": "your-subscription-id",
    "resource_group": "legal-rag-personal-rg",
    "workspace_name": "legal-rag-ml-workspace"
}
```

### Step 5: Update Azure DevOps Pipeline

Add Azure ML logging to your monitoring pipeline:

```yaml
# In azure-pipelines-monitoring.yml

- script: |
    python evaluate_rag.py --output monitoring_eval_$(Build.BuildId).json
  displayName: 'Run full evaluation with Azure ML tracking'
  env:
    PINECONE_API_KEY: $(PINECONE_API_KEY)
    ANTHROPIC_API_KEY: $(ANTHROPIC_API_KEY)
    OPENAI_API_KEY: $(OPENAI_API_KEY)
    EMBEDDING_PROVIDER: openai
    AZURE_ML_TRACKING: true  # Enable Azure ML logging
```

Add pipeline variables in Azure DevOps:
- Go to your monitoring pipeline
- Edit → Variables
- Add from config.json:
  - `AZURE_SUBSCRIPTION_ID`
  - `AZURE_ML_WORKSPACE`
  - `AZURE_ML_RESOURCE_GROUP`

Update the script to create config.json dynamically:

```yaml
- script: |
    echo "{" > config.json
    echo "  \"subscription_id\": \"$(AZURE_SUBSCRIPTION_ID)\"," >> config.json
    echo "  \"resource_group\": \"$(AZURE_ML_RESOURCE_GROUP)\"," >> config.json
    echo "  \"workspace_name\": \"$(AZURE_ML_WORKSPACE)\"" >> config.json
    echo "}" >> config.json
  displayName: 'Create Azure ML config'
```

## Where to View Your Metrics

### Azure ML Studio (Best for Experimentation & Monitoring)

1. **Go to**: [https://ml.azure.com](https://ml.azure.com)
2. **Select**: Your workspace (`legal-rag-ml-workspace`)

#### View Individual Runs:

**Path**: Experiments → `legal-rag-evaluation` → Runs

You'll see a table with all evaluation runs:

| Run ID | Status | Precision@5 | Citation Accuracy | Latency | Cost | Date |
|--------|--------|-------------|-------------------|---------|------|------|
| Run_1  | Completed | 0.85 | 0.97 | 5.2s | $0.013 | Dec 3 |
| Run_2  | Completed | 0.83 | 0.96 | 5.5s | $0.014 | Dec 4 |
| Run_3  | Completed | 0.78 | 0.95 | 6.1s | $0.015 | Dec 5 |

Click any run to see:
- **Overview**: All metrics at a glance
- **Metrics**: Interactive charts (line plots, scatter plots)
- **Outputs + logs**: Download evaluation_results.json
- **Snapshots**: Code version that generated this run

#### Compare Multiple Runs:

1. Select 2+ runs (checkboxes)
2. Click **"Compare"**
3. See side-by-side comparison:
   - Metric differences highlighted
   - Charts overlaid
   - Easy to spot regressions

**Example**:
```
Comparing Run_1 vs Run_3:
❌ Precision@5: 0.85 → 0.78 (-8.2%)
❌ Latency: 5.2s → 6.1s (+17.3%)
✅ Citation Accuracy: 0.97 → 0.95 (-2.1%)
```

#### View Trends Over Time:

**Path**: Experiments → `legal-rag-evaluation` → Charts

Create custom visualizations:
1. Click **"Add chart"**
2. X-axis: `run_number` or `timestamp`
3. Y-axis: `precision@5`
4. Chart type: Line chart

Pin charts to create a **monitoring dashboard**!

### Azure Application Insights (Best for Real-Time Production)

Application Insights is automatically created with your ML workspace.

**Path**: Azure Portal → Application Insights → `legal-rag-ml-workspace-insights`

#### View Live Metrics:

**Path**: Live Metrics

Real-time dashboard showing:
- Incoming requests per second
- Request duration
- Failure rate
- CPU/Memory usage

#### Custom Metrics:

**Path**: Metrics → Add metric

Create charts for:
- RAG query rate (requests/min)
- Average latency trend
- Error rate percentage
- API cost per hour

#### Alerts:

**Path**: Alerts → New alert rule

Set up alerts:
1. **Condition**: "Whenever average latency is greater than 10s"
2. **Check every**: 5 minutes
3. **Action**: Send email to you
4. **Save**

You'll get emails when quality degrades!

### Azure Dashboards (Best for Stakeholder Reporting)

**Path**: Azure Portal → Dashboards → New dashboard

Create a custom dashboard with:
1. **ML Experiment metrics** (precision, latency, cost)
2. **Application Insights metrics** (request rate, errors)
3. **Cost Analysis** (spending trends)
4. **Resource Health** (AKS pod status)

Pin this dashboard and share URL with stakeholders!

## Experimentation Workflow

### Comparing Different Models

When you want to test OpenAI vs Cohere embeddings:

```bash
# Baseline: OpenAI embeddings
export EMBEDDING_PROVIDER=openai
python evaluate_rag.py
# Logs to Azure ML as Run_1

# Experiment: Cohere embeddings
export EMBEDDING_PROVIDER=cohere
python evaluate_rag.py
# Logs to Azure ML as Run_2

# Compare in Azure ML Studio
# Go to Experiments → Select Run_1 and Run_2 → Compare
```

Azure ML shows:
```
OpenAI vs Cohere:
- Precision@5: 0.85 vs 0.80 (OpenAI wins by 6%)
- Latency: 5.2s vs 4.8s (Cohere faster by 8%)
- Cost: $0.013 vs $0.009 (Cohere cheaper by 31%)
```

### Tracking Prompt Changes

Add tags to runs:

```python
# In evaluate_rag.py
self.run.tag("prompt_version", "v2")
self.run.tag("embedding_model", "text-embedding-3-small")
self.run.tag("llm_model", "claude-sonnet-4.5")
```

Filter runs by tag in Azure ML Studio to see impact of specific changes.

### A/B Testing in Production

Log every production query to Azure ML:

```python
# In api.py
from azureml.core import Workspace, Experiment

ws = Workspace.from_config()
experiment = Experiment(workspace=ws, name="legal-rag-production")

@app.post("/api/query")
async def query(request: QueryRequest):
    run = experiment.start_logging()

    # ... process query ...

    # Log production metrics
    run.log("latency", latency)
    run.log("num_retrieved_cases", len(retrieved_cases))
    run.log("answer_length", len(answer))
    run.log("user_query_length", len(request.query))

    run.complete()
    return response
```

View production metrics in real-time in Azure ML!

## Cost Breakdown

### Azure ML Workspace:
- **Basic tier**: ~$10/month
- **Storage**: ~$2/month (for experiment artifacts)
- **Application Insights**: ~$5/month (first 5GB free)
- **Total**: ~$17/month

### Alternative: Use FREE Tier

Weights & Biases (FREE tier) gives you similar functionality:
- Unlimited experiments
- Team collaboration (up to 2 people)
- 100GB storage
- **Cost**: $0

To use W&B instead:
```python
import wandb

# In evaluate_rag.py
wandb.init(project="legal-rag-monitoring")
wandb.log({
    "precision@5": 0.85,
    "citation_accuracy": 0.97,
    "latency": 5.2
})
```

View at: [wandb.ai/your-project/legal-rag-monitoring](https://wandb.ai)

## Recommendation

**For interviews/personal projects**: Start with **Weights & Biases (FREE)**
- Zero cost, professional-looking dashboards
- Easy to set up (5 minutes)
- Great for showing in interviews

**For production/enterprise**: Use **Azure ML + Application Insights**
- Integrated with your Azure infrastructure
- Better for compliance/security
- Stakeholders prefer staying in Azure ecosystem

**Best of both worlds**: Use both!
- W&B for experimentation and development
- Azure ML for production monitoring

## Next Steps

### Option 1: Quick Start with Weights & Biases (5 minutes)

```bash
# 1. Install
pip install wandb

# 2. Login
wandb login

# 3. Add to evaluate_rag.py
import wandb
wandb.init(project="legal-rag")
# ... after evaluation ...
wandb.log(self.results["retrieval_metrics"])

# 4. Run evaluation
python evaluate_rag.py

# 5. View at wandb.ai
```

### Option 2: Full Azure ML Setup (30 minutes)

1. ✅ Create Azure ML workspace (done above)
2. ✅ Download config.json
3. ✅ Update evaluate_rag.py with logging code
4. ✅ Update Azure DevOps pipeline
5. Run evaluation and view in Azure ML Studio

## Interview Talking Points

**"Where do you monitor your models?"**

> "I use Azure Machine Learning workspace for comprehensive monitoring and
> experimentation. Every evaluation run is automatically logged with metrics
> like Precision@5, latency, and cost. I can view trends over time, compare
> different model configurations side-by-side, and get alerts when quality
> degrades.
>
> For example, when I tested OpenAI vs Cohere embeddings, Azure ML showed me
> that OpenAI had 6% better Precision@5 but Cohere was 31% cheaper and 8%
> faster. This data-driven comparison helped me make the right tradeoff.
>
> I also have Azure Application Insights tracking real-time production metrics
> with alerts set up - if latency exceeds 10 seconds, I get an email immediately."

**"How do you track experiments?"**

> "Every model change is logged as an experiment run in Azure ML. I tag each run
> with metadata like prompt_version, embedding_model, and llm_model. This lets me
> filter runs to see the impact of specific changes. For instance, I can pull up
> all runs using 'claude-sonnet-4.5' vs 'claude-haiku' and compare cost/quality
> tradeoffs.
>
> I also run scheduled daily evaluations on 50 curated test queries, so I can
> detect quality regressions over time. The Azure ML charts show me if
> Precision@5 is trending down, which triggers an investigation."

---

**Ready to go!** Choose W&B (free, 5 min) or Azure ML (paid, 30 min) and start monitoring.
