# 🚂 Railway Deployment Guide - Full App with Your Data

This guide will deploy your complete audio transcription dashboard to Railway with all your existing functionality and data.

## ✅ What You Get with Railway

- **Full Flask App**: All your original features and functionality
- **Real Data**: Uses your existing CSV file with 172+ call records
- **Persistent Storage**: Your data survives deployments
- **Background Processing**: Audio transcription with Deepgram & OpenAI
- **24/7 Uptime**: No cold starts like other free platforms
- **$5/month credit**: Usually enough for most usage

## 🚀 Step-by-Step Deployment

### Step 1: Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Click "Login" and sign in with GitHub
3. Authorize Railway to access your GitHub account

### Step 2: Deploy Your Repository

1. **Click "New Project"** in Railway dashboard
2. **Select "Deploy from GitHub repo"**
3. **Choose your repository**: `apolead/call_dashboiard`
4. **Railway will automatically detect it's a Python app**
5. **Click "Deploy"** - it will start building immediately

### Step 3: Configure Environment Variables

**IMPORTANT**: Add these environment variables in Railway:

1. **In your Railway project**, click on your service
2. **Go to "Variables" tab**
3. **Add these variables:**

#### Required Variables:
```
DEEPGRAM_API_KEY=your_deepgram_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=railway-super-secret-key-2024
```

#### Optional Variables (with defaults):
```
OPENAI_MODEL=gpt-3.5-turbo
DEBUG_MODE=False
COMPANY_NAME=ApoLead
PRIMARY_COLOR=#1e40af
SECONDARY_COLOR=#3b82f6
ACCENT_COLOR=#06b6d4
```

#### AWS S3 Variables (if using S3):
```
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_BUCKET_NAME=combined-client-data
AWS_PREFIX=c_30214/XC_Recordings/
AWS_REGION=us-east-1
ENABLE_S3_SYNC=True
```

### Step 4: Upload Your Data (Important!)

Since Railway doesn't automatically include your local files, you need to upload your CSV data:

**Option A: Include in Repository (Recommended)**
```bash
# In your local project folder
cp data/call_transcriptions.csv ./
git add call_transcriptions.csv
git commit -m "Add existing call data for Railway deployment"
git push origin main
```

**Option B: Manual Upload via Railway Dashboard**
1. Go to your Railway project
2. Open the deployment logs
3. Use Railway's file manager to upload your CSV

### Step 5: Verify Deployment

1. **Wait for build to complete** (usually 3-5 minutes)
2. **Railway will provide a URL** like: `https://your-app-name.railway.app`
3. **Visit your dashboard** - you should see:
   - All your existing data (172+ records)
   - Working charts and analytics
   - Intent sub-category breakdown (3 per row)
   - Disposition filtering
   - All interactive features

## 🔧 Configuration Files Explained

### `railway.json`
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python app.py",
    "healthcheckPath": "/",
    "healthcheckTimeout": 30
  }
}
```

### `Procfile`
```
web: python app.py
```

### `requirements.txt`
Contains all your original dependencies:
- flask, deepgram-sdk, openai, pandas, boto3, etc.

## 🎯 Features That Work on Railway

- ✅ **Full Dashboard**: All charts, analytics, and UI features
- ✅ **Real Data**: Your existing 172 call records
- ✅ **Audio Processing**: Deepgram transcription (if API key provided)
- ✅ **AI Analysis**: OpenAI intent classification and summaries
- ✅ **S3 Integration**: Sync with your existing audio files
- ✅ **Background Processing**: File monitoring and batch processing
- ✅ **Disposition Tracking**: Primary/secondary disposition analytics
- ✅ **Responsive Design**: Works on all devices
- ✅ **Data Persistence**: CSV data survives deployments

## 💰 Cost Breakdown

- **Free**: $5 credit per month (usually sufficient)
- **If you exceed**: $5/month for continued usage
- **No surprise charges**: Railway clearly shows usage

## 🔍 Troubleshooting

### Common Issues:

**1. Build Fails**
- Check that all environment variables are set
- Verify your requirements.txt is properly formatted

**2. No Data Showing**
- Make sure `call_transcriptions.csv` is in the repository
- Check the health endpoint: `https://your-app.railway.app/health`

**3. API Errors**
- Verify your API keys are correctly set in environment variables
- Check Railway logs for specific error messages

**4. File Upload Issues**
- Ensure your CSV file is committed to the repository
- Check file permissions and paths

### Debug Commands:

**View Logs**:
- In Railway dashboard → your service → "Deployments" → "View Logs"

**Check Health**:
- Visit: `https://your-app-name.railway.app/health`
- Should show: data_file_exists: true, total_records: 172+

**Environment Check**:
- Railway dashboard → your service → "Variables"

## 🚀 After Deployment

Once deployed, you'll have:

1. **Live URL**: `https://your-app-name.railway.app`
2. **Real-time Dashboard**: With all your existing data
3. **API Endpoints**: All working with your data
4. **Background Processing**: For new audio files
5. **Admin Features**: Classification, processing controls

## 🔄 Updating Your App

To update after changes:
```bash
git add .
git commit -m "Update dashboard features"
git push origin main
```

Railway automatically redeploys on every push to main branch.

## 🎉 Success!

Your dashboard should now be live with:
- All 172+ call records
- Working analytics and charts
- Intent sub-category breakdown (3 per row)
- Disposition filtering and classification
- Full audio processing capabilities

**Your Railway URL**: `https://your-app-name.railway.app`

---

Need help? Check Railway's excellent documentation or reach out to their support - they're very responsive!