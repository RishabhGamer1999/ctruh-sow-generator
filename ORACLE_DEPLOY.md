# 🌐 Deploying SOP / SOW Generator to Oracle Cloud (Always Free)

This guide walks you through hosting the SOP Generator on Oracle Cloud's **Always Free** tier — accessible from any device, anywhere, 24/7. No cost, ever.

---

## Step 1 — Create a Free Oracle Cloud Account

1. Go to **https://cloud.oracle.com/free**
2. Click **Start for free**
3. Fill in your details (requires a credit card for identity verification, but you will NOT be charged)
4. Verify your email and complete signup

---

## Step 2 — Create Your Free Server (VM Instance)

1. Log in to Oracle Cloud at **https://cloud.oracle.com**
2. In the top search bar, type **"Instances"** and click it
3. Click **Create Instance**
4. Fill in:
   - **Name**: `sop-generator` (or anything you like)
   - **Image**: Keep default (Oracle Linux)
   - **Shape**: Click **Change Shape** → select **Ampere** → choose:
     - **OCPUs**: 4
     - **Memory**: 24 GB
   - **SSH Keys**: Click **Generate a key pair** and **download both files** (you'll need these to connect)
5. Click **Create**
6. Wait 2-3 minutes for the instance to start

---

## Step 3 — Open the Firewall Port

1. Click on your new instance name
2. Scroll down → click **Subnet** link
3. Click **Security List** → **Add Ingress Rules**
4. Add this rule:
   - Source CIDR: `0.0.0.0/0`
   - Destination Port: `8501`
5. Click **Add Ingress Rules**

---

## Step 4 — Connect to Your Server

On your Windows PC:
1. Press `Windows key` → type `cmd` → press Enter
2. Run this command (replace with your actual file path and server IP):

```
ssh -i C:\Users\YourName\Downloads\ssh-key.key opc@YOUR_SERVER_IP
```

You'll find your server's IP in the Oracle Console under your instance details.

---

## Step 5 — Install Docker on the Server

Once connected, paste these commands one by one:

```bash
# Install Docker
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker opc

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Open firewall on server side
sudo firewall-cmd --permanent --add-port=8501/tcp
sudo firewall-cmd --reload
```

Log out and log back in for the Docker group change to take effect.

---

## Step 6 — Upload the Project

On your Windows PC, open Command Prompt and run:

```
scp -i C:\Users\YourName\Downloads\ssh-key.key -r C:\path\to\sop-generator opc@YOUR_SERVER_IP:~/sop-generator
```

---

## Step 7 — Start the App

On the server (via SSH):

```bash
cd ~/sop-generator
docker-compose up -d

# Pull AI models (one-time, ~4-5 GB)
docker exec sop-ollama ollama pull mistral:7b
docker exec sop-ollama ollama pull nomic-embed-text
```

---

## Step 8 — Access the App

Open any browser on any device and go to:

```
http://YOUR_SERVER_IP:8501
```

That's it! The app is now live 24/7. 🎉

---

## Uploading Your Knowledge Base

To add documents to the knowledge base on the server:

```bash
# From your Windows PC
scp -i C:\Users\YourName\Downloads\ssh-key.key "C:\path\to\your\sop.docx" opc@YOUR_SERVER_IP:~/sop-generator/knowledge_base/past_sops/
```

Then click **Re-index Knowledge Base** in the app sidebar.

---

## Tips

- **Stop the app**: `docker-compose down` (on the server)
- **View logs**: `docker-compose logs -f app`
- **Update the app**: Re-upload changed files via `scp`, then `docker-compose up -d --build`
- Your server IP stays the same (it's a static IP on Oracle Cloud)
