# ☁️ Amazon AWS Hosting Guide — BuildMetrics AI v2.0.0

This guide provides three tested, production-grade deployment strategies for hosting **BuildMetrics AI** on Amazon Web Services (AWS).

---

## 🚀 Comparison of AWS Hosting Options

| Strategy | Best For | AWS Services | Setup Time | Monthly Cost (Est.) |
| :--- | :--- | :--- | :---: | :---: |
| **Option 1: 1-Click CloudFormation (Recommended)** | Quick showcase, full Docker stack, automated setup | EC2 (t3.medium), VPC, Security Group | ~3 minutes | ~$30 / month (or Free Tier t3.micro/small) |
| **Option 2: AWS App Runner (Serverless)** | Production scale, auto-SSL, zero server maintenance | App Runner, ECR | ~5 minutes | Pay-per-request / vCPU |
| **Option 3: Manual EC2 with UserData** | Full control, custom domain, Nginx reverse proxy | EC2, Docker Compose | ~5 minutes | ~$15–$30 / month |

---

## ⚡ Option 1: 1-Click AWS CloudFormation Deployment (Easiest)

We provide an automated CloudFormation template located at [`aws/cloudformation.yml`](aws/cloudformation.yml).

### Step-by-Step Instructions:

1. **Sign In to AWS Console**: Open [AWS Management Console](https://console.aws.amazon.com/).
2. **Navigate to CloudFormation**: Search for **CloudFormation** in the top search bar.
3. **Create Stack**:
   - Click **Create stack** > **With new resources (standard)**.
   - Under **Prerequisite - Prepare template**, select **Template is ready**.
   - Under **Specify template**, select **Upload a template file**.
   - Choose the file [`aws/cloudformation.yml`](aws/cloudformation.yml) from this project.
   - Click **Next**.
4. **Specify Stack Details**:
   - **Stack name**: `BuildMetrics-AI-Stack`
   - **InstanceType**: Select `t3.medium` (or `t3.small` for lighter testing).
   - **KeyName**: Select your existing EC2 Key Pair (or leave empty if you don't need SSH).
   - **GeminiApiKey**: (Optional) Enter your Google Gemini API Key.
   - Click **Next** > **Next** > **Submit**.
5. **Wait for Stack Creation (~3 minutes)**:
   - CloudFormation will provision the VPC security group, launch the EC2 instance, install Docker, clone the repository, and start the container stack.
6. **Access Your Live App**:
   - Once status shows `CREATE_COMPLETE`, click on the **Outputs** tab.
   - Click on the **StreamlitStudioURL** link: `http://<EC2-Public-IP>:8501`.
   - Click on the **FastApiDocsURL** link: `http://<EC2-Public-IP>:8000/docs`.

---

## 🖥️ Option 2: Launch via AWS CLI (Single Command)

If you have configured AWS CLI (`aws configure`), you can launch the entire stack in one terminal command:

```bash
aws cloudformation create-stack \
  --stack-name BuildMetrics-AI-Stack \
  --template-body file://aws/cloudformation.yml \
  --parameters ParameterKey=InstanceType,ParameterValue=t3.medium \
  --capabilities CAPABILITY_IAM
```

To monitor stack progress:
```bash
aws cloudformation describe-stacks --stack-name BuildMetrics-AI-Stack --query "Stacks[0].StackStatus"
```

To get your live application URLs when finished:
```bash
aws cloudformation describe-stacks --stack-name BuildMetrics-AI-Stack --query "Stacks[0].Outputs"
```

---

## 🌐 Option 3: AWS App Runner (Serverless Container with HTTPS)

AWS App Runner runs containers with automatic load balancing, HTTPS TLS certificates, and zero infrastructure maintenance.

1. In AWS Console, go to **AWS App Runner**.
2. Click **Create service**.
3. **Source**: Select **Source code repository** (Connect your GitHub account) or **Container registry** (Amazon ECR).
4. **Repository**: Select `shambhushekharsinha-engg/BuildMetrics-AI`, branch `main`.
5. **Configuration**:
   - Configuration file: Select **Use a configuration file** (it automatically detects [`aws/apprunner.yaml`](aws/apprunner.yaml)).
6. **Service settings**:
   - Service name: `buildmetrics-ai`
   - vCPU: `1 vCPU`, Memory: `2 GB`
7. Click **Create & deploy**.
8. App Runner will give you a default HTTPS URL (e.g. `https://xyz.awsapprunner.com`).

---

## 🔒 Security & Firewall Ports

The CloudFormation template and EC2 deployment configure the following firewall rules:

| Port | Protocol | Purpose | Access |
| :--- | :---: | :--- | :--- |
| `8501` | TCP | Streamlit Architectural Studio UI | Public (`0.0.0.0/0`) |
| `8000` | TCP | FastAPI REST API & Swagger UI (`/docs`) | Public (`0.0.0.0/0`) |
| `80` | TCP | Standard HTTP Web Traffic | Public (`0.0.0.0/0`) |
| `443` | TCP | Secure HTTPS Web Traffic | Public (`0.0.0.0/0`) |
| `22` | TCP | SSH Shell Administration | Restrict to your IP |

---

## 🔄 Updating Your Live AWS Deployment

To deploy updates after pushing code changes to GitHub:

### If using EC2:
```bash
ssh -i your-key.pem ubuntu@<EC2-PUBLIC-IP>
cd /home/ubuntu/BuildMetrics-AI  # or /opt/buildmetrics-ai
git pull origin main
docker compose up -d --build
```

### If using AWS App Runner:
App Runner automatically redeploys whenever new commits are pushed to the `main` branch.
