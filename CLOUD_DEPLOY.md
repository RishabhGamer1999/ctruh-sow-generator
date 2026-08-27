# ☁️ Deploying CTRUH SOW Generator (100% Free, 24/7, No Credit Card)

Follow these 3 simple steps to have your SOW Generator running in the cloud 24/7.
Once deployed, you can access it from your office PC, phone, or home with your personal laptop completely turned OFF.

---

## Step 1: Get Your Free Groq API Key (30 Seconds)

1. Open **[console.groq.com](https://console.groq.com)** in your browser.
2. Sign in with your Google account (100% free, **no credit card needed**).
3. In the left sidebar, click on **API Keys**.
4. Click **Create API Key**, give it a name (e.g. `ctruh-sow`), and **copy the key** (starts with `gsk_...`).
5. Save it in your notes — you will paste this in Step 3.

---

## Step 2: Create a GitHub Repository & Upload Files

1. Go to **[github.com](https://github.com)** and log in (or create a free account).
2. Click the **`+`** icon in the top-right corner → **New repository**.
3. Name it: `ctruh-sow-generator`.
4. Set it to **Private** (or Public, as you prefer).
5. Click **Create repository**.
6. On the next screen, click the link that says: **"uploading an existing file"**.
7. Drag and drop all the files from your folder (`C:\Users\risha\.gemini\antigravity\scratch\sop-generator`):
   - `streamlit_app.py`
   - `requirements.txt`
   - `README.md`
   - The entire `app/` folder
   - The entire `knowledge_base/` folder
8. Click **Commit changes**.

---

## Step 3: 1-Click Deploy on Streamlit Community Cloud

1. Go to **[share.streamlit.io](https://share.streamlit.io)**.
2. Click **Continue with GitHub** to log in.
3. Click **Create app** (or "New app").
4. Select your repository: `your-username/ctruh-sow-generator`.
5. Set:
   - **Main file path**: `streamlit_app.py`
   - **App URL**: `ctruh-sow-generator` (or whatever custom name you want)
6. Click **Advanced settings...** (below the deploy button):
   - In the **Secrets** box, paste:
     ```toml
     GROQ_API_KEY = "gsk_your_actual_key_here"
     ```
7. Click **Save** → then click **Deploy!**

---

## 🎉 You're Live!

In about 1-2 minutes, your web application will be live at:
```
https://ctruh-sow-generator.streamlit.app
```

- ✅ Works from **any device** (Office laptop, home PC, mobile).
- ✅ **Your personal laptop can be turned OFF**.
- ✅ **\$0 cost forever**, zero credit cards entered anywhere.
