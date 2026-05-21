# Flask Calculation API — Full Deployment Guide
### Python Flask · Docker · GitHub Actions · AWS ECR + ECS Fargate

---

## Repository Structure

```
flask-calc-api/
├── app.py                        # Flask application & routes
├── calculator.py                 # Business logic
├── requirements.txt
├── Dockerfile                    # Multi-stage build
├── docker-compose.yml            # Local development
├── ecs-task-definition.json      # ECS task definition template
├── .gitignore
├── tests/
│   └── test_app.py               # Pytest unit tests
└── .github/
    └── workflows/
        └── deploy.yml            # CI/CD pipeline
```

---

## API Endpoints

| Method | Endpoint            | Body                    | Description       |
|--------|---------------------|-------------------------|-------------------|
| GET    | `/health`           | —                       | Health check      |
| POST   | `/api/v1/add`       | `{"a": 10, "b": 5}`    | Addition          |
| POST   | `/api/v1/subtract`  | `{"a": 10, "b": 5}`    | Subtraction       |
| POST   | `/api/v1/multiply`  | `{"a": 4, "b": 5}`     | Multiplication    |
| POST   | `/api/v1/divide`    | `{"a": 10, "b": 2}`    | Division          |
| POST   | `/api/v1/power`     | `{"a": 2, "b": 10}`    | Power / Exponent  |
| POST   | `/api/v1/sqrt`      | `{"a": 25}`             | Square Root       |

**Sample request:**
```bash
curl -X POST http://localhost:5000/api/v1/add \
     -H "Content-Type: application/json" \
     -d '{"a": 10, "b": 5}'

# Response: {"operation":"add","a":10,"b":5,"result":15}
```

---

## Part 1 — Local Development

```bash
# 1. Clone and enter the project
git clone https://github.com/<YOUR_USERNAME>/flask-calc-api.git
cd flask-calc-api

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run tests
pytest tests/ -v

# 5. Start the dev server
python app.py                     # visits http://localhost:5000

# 6. Or run with Docker Compose
docker compose up --build
```

---

## Part 2 — GitHub Repository Setup

### 2.1 Create and push the repository

```bash
cd flask-calc-api
git init
git add .
git commit -m "feat: initial flask calc api"

# Create repo on GitHub (via gh CLI or github.com UI), then:
git remote add origin https://github.com/<YOUR_USERNAME>/flask-calc-api.git
git branch -M main
git push -u origin main
```

### 2.2 Add GitHub Actions Secrets

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**

| Secret Name              | Value                                   |
|--------------------------|-----------------------------------------|
| `AWS_ACCESS_KEY_ID`      | IAM user access key (from Part 3)       |
| `AWS_SECRET_ACCESS_KEY`  | IAM user secret key (from Part 3)       |

> ⚠️ Never commit AWS credentials to your repository.

### 2.3 Update environment variables in deploy.yml

Open `.github/workflows/deploy.yml` and edit the `env:` block at the top:

```yaml
env:
  AWS_REGION: us-east-1           # your AWS region
  ECR_REPOSITORY: calc-api        # must match ECR repo name
  ECS_CLUSTER: calc-api-cluster   # your ECS cluster name
  ECS_SERVICE: calc-api-service   # your ECS service name
  CONTAINER_NAME: calc-api        # matches ecs-task-definition.json
```

---

## Part 3 — AWS Account Setup (Step-by-Step)

### 3.1 Create an IAM User for GitHub Actions

1. Open **AWS Console → IAM → Users → Create user**
2. Username: `github-actions-deployer`
3. Select **"Attach policies directly"**
4. Attach these managed policies:
   - `AmazonEC2ContainerRegistryFullAccess`
   - `AmazonECS_FullAccess`
5. Click **Create user**
6. Go to the user → **Security credentials → Create access key**
7. Choose **"Application running outside AWS"**
8. **Copy the Access Key ID and Secret Access Key** → paste into GitHub Secrets (Step 2.2)

---

### 3.2 Create an ECR Repository

```bash
# Using AWS CLI (or do this in the Console)
aws ecr create-repository \
    --repository-name calc-api \
    --region us-east-1
```

**Console steps:**
1. Open **Amazon ECR → Repositories → Create repository**
2. Name: `calc-api`
3. Visibility: **Private**
4. Click **Create repository**
5. Copy the **URI** — format: `<ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/calc-api`

---

### 3.3 Create an ECS Cluster

```bash
aws ecs create-cluster \
    --cluster-name calc-api-cluster \
    --capacity-providers FARGATE \
    --region us-east-1
```

**Console steps:**
1. Open **Amazon ECS → Clusters → Create cluster**
2. Name: `calc-api-cluster`
3. Infrastructure: **AWS Fargate (serverless)**
4. Click **Create**

---

### 3.4 Create the ECS Task Execution IAM Role

This role allows ECS to pull images from ECR and write logs to CloudWatch.

```bash
# Create the role
aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document '{
    "Version":"2012-10-17",
    "Statement":[{
      "Effect":"Allow",
      "Principal":{"Service":"ecs-tasks.amazonaws.com"},
      "Action":"sts:AssumeRole"
    }]
  }'

# Attach the managed policy
aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

**Console steps:**
1. Open **IAM → Roles → Create role**
2. Trusted entity: **AWS service → Elastic Container Service Task**
3. Attach policy: `AmazonECSTaskExecutionRolePolicy`
4. Role name: `ecsTaskExecutionRole`
5. Click **Create role**

---

### 3.5 Create a CloudWatch Log Group

```bash
aws logs create-log-group \
    --log-group-name /ecs/calc-api \
    --region us-east-1
```

**Console:** CloudWatch → Log groups → Create log group → `/ecs/calc-api`

---

### 3.6 Update and Register the ECS Task Definition

1. Open `ecs-task-definition.json` and replace ALL placeholders:

| Placeholder       | Replace with                                  |
|-------------------|-----------------------------------------------|
| `<ACCOUNT_ID>`    | Your 12-digit AWS account ID                  |
| `<AWS_REGION>`    | e.g. `us-east-1`                              |

2. Register the task definition:

```bash
aws ecs register-task-definition \
    --cli-input-json file://ecs-task-definition.json \
    --region us-east-1
```

---

### 3.7 Create a VPC Security Group (for the ECS tasks)

```bash
# Get your default VPC ID
VPC_ID=$(aws ec2 describe-vpcs \
    --filters Name=isDefault,Values=true \
    --query 'Vpcs[0].VpcId' --output text)

# Create security group
SG_ID=$(aws ec2 create-security-group \
    --group-name calc-api-sg \
    --description "Allow port 5000" \
    --vpc-id $VPC_ID \
    --query 'GroupId' --output text)

# Allow inbound traffic on port 5000
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 5000 \
    --cidr 0.0.0.0/0

echo "Security Group ID: $SG_ID"
```

---

### 3.8 Create the ECS Service

Replace `<SUBNET_ID_1>`, `<SUBNET_ID_2>`, and `<SG_ID>` with your actual values.

```bash
aws ecs create-service \
    --cluster calc-api-cluster \
    --service-name calc-api-service \
    --task-definition calc-api \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={
        subnets=[<SUBNET_ID_1>,<SUBNET_ID_2>],
        securityGroups=[<SG_ID>],
        assignPublicIp=ENABLED
    }" \
    --region us-east-1
```

**Console steps:**
1. Open **ECS → Clusters → calc-api-cluster → Services → Create**
2. Launch type: **Fargate**
3. Task definition: `calc-api` (latest revision)
4. Service name: `calc-api-service`
5. Desired tasks: `1`
6. Networking: select your VPC, at least 2 subnets, the security group created above
7. Auto-assign public IP: **Enabled**
8. Click **Create**

---

## Part 4 — Pipeline Execution Flow

```
git push → main
    │
    ▼
GitHub Actions: deploy.yml
    │
    ├─ JOB 1: test
    │     └── pytest tests/ -v
    │
    └─ JOB 2: build-and-deploy  (only if tests pass + branch = main)
          │
          ├── aws-actions/configure-aws-credentials
          ├── aws-actions/amazon-ecr-login
          ├── docker build + docker push  →  ECR
          ├── aws-actions/amazon-ecs-render-task-definition
          └── aws-actions/amazon-ecs-deploy-task-definition
                └── Updates ECS service → new task starts → old task drains
```

### Triggering a deployment

```bash
# Any push to main triggers the full pipeline:
git add .
git commit -m "fix: update calculation logic"
git push origin main
```

Monitor in **GitHub → Actions tab** and **AWS → ECS → calc-api-cluster → calc-api-service → Tasks**.

---

## Part 5 — Verify the Deployment

1. Open **ECS → Clusters → calc-api-cluster → Tasks**
2. Click the running task → find the **Public IP**
3. Test:

```bash
# Health check
curl http://<TASK_PUBLIC_IP>:5000/health

# Addition
curl -X POST http://<TASK_PUBLIC_IP>:5000/api/v1/add \
     -H "Content-Type: application/json" \
     -d '{"a": 42, "b": 8}'
```

---

## Part 6 — Optional: Add an Application Load Balancer

For production, add an ALB in front of your ECS service:

1. **EC2 → Load Balancers → Create → Application Load Balancer**
2. Listener: HTTP port 80
3. Target group: IP type, port 5000, health check path `/health`
4. Associate the target group with your ECS service (edit service → Load balancing)
5. Access the API via the ALB DNS name instead of the task IP

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| ECR push fails | Verify `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` secrets are set correctly |
| Task keeps stopping | Check CloudWatch Logs `/ecs/calc-api` for errors |
| Cannot reach the API | Confirm the security group allows inbound TCP 5000 and the task has a public IP |
| `ecsTaskExecutionRole` not found | Re-run Step 3.4 to create the IAM role |
| GitHub Actions: `service not found` | Check `ECS_SERVICE` and `ECS_CLUSTER` env vars match exactly |
