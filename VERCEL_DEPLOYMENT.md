# Vercel Deployment Guide

This guide will help you deploy the Audio Transcription Dashboard to Vercel via GitHub.

## Prerequisites

1. GitHub account
2. Vercel account (connect with GitHub)
3. API keys for:
   - Deepgram API
   - OpenAI API
   - AWS S3 (optional)

## Step 1: Prepare Your Repository

1. **Fork or clone this repository to your GitHub account**

2. **Push all files to your GitHub repository**, including:
   - `vercel.json` - Vercel configuration
   - `api/index.py` - Serverless entry point
   - `app_vercel.py` - Serverless-optimized Flask app
   - `config_vercel.py` - Serverless configuration
   - `requirements-vercel.txt` - Python dependencies
   - `.env.example` - Environment variables template

## Step 2: Deploy to Vercel

### Option A: Deploy via Vercel Dashboard

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click "New Project"
3. Import your GitHub repository
4. Vercel will automatically detect this as a Python project
5. Click "Deploy"

### Option B: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy from project directory
vercel --prod
```

## Step 3: Configure Environment Variables

After deployment, add these environment variables in your Vercel dashboard:

### Required Variables

- `DEEPGRAM_API_KEY` - Your Deepgram API key
- `OPENAI_API_KEY` - Your OpenAI API key
- `SECRET_KEY` - A secure random string for Flask sessions

### Optional Variables

- `OPENAI_MODEL` - Default: `gpt-3.5-turbo`
- `DEBUG_MODE` - Default: `False`
- `COMPANY_NAME` - Default: `ApoLead`
- `PRIMARY_COLOR` - Default: `#1e40af`
- `SECONDARY_COLOR` - Default: `#3b82f6`
- `ACCENT_COLOR` - Default: `#06b6d4`

### AWS S3 Variables (Optional)

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_BUCKET_NAME`
- `AWS_PREFIX`
- `AWS_REGION`
- `ENABLE_S3_SYNC` - Default: `True`

## Step 4: Configure Environment Variables in Vercel

1. Go to your project in Vercel dashboard
2. Navigate to "Settings" → "Environment Variables"
3. Add each variable with its value
4. Set the environment to "Production" (and "Preview" if needed)
5. Click "Save"

## Step 5: Redeploy

After adding environment variables:

1. Go to the "Deployments" tab
2. Click the "..." menu on the latest deployment
3. Select "Redeploy"

## Key Differences from Local Version

### Serverless Adaptations

- **No File Processing**: The serverless version is read-only for demo purposes
- **In-Memory Data**: Uses sample data instead of processing real audio files
- **Mock Services**: Some features are mocked for demonstration
- **Temp Directories**: Uses system temp directories instead of persistent storage

### What Works in Serverless

- ✅ Dashboard UI with all charts and analytics
- ✅ Sample data visualization
- ✅ Responsive design and all interactive features
- ✅ Intent and disposition analytics
- ✅ All chart types and filtering
- ✅ Modal views and transcription display

### What's Limited in Serverless

- ❌ Real audio file processing (would need background jobs)
- ❌ File uploads (no persistent storage)
- ❌ Real-time processing status
- ❌ Large file handling

## Custom Domain (Optional)

1. In Vercel dashboard, go to "Settings" → "Domains"
2. Add your custom domain
3. Update DNS settings as instructed by Vercel

## Monitoring and Logs

- View deployment logs in Vercel dashboard
- Monitor function performance and usage
- Set up alerts for errors or downtime

## Local Development with Serverless Config

To test the serverless version locally:

```bash
# Use the Vercel config
python app_vercel.py
```

## Troubleshooting

### Common Issues

1. **Build Failures**: Check `requirements-vercel.txt` for incompatible packages
2. **Environment Variables**: Ensure all required variables are set
3. **Import Errors**: Check Python path configuration in `api/index.py`
4. **Memory Limits**: Vercel has memory limits for serverless functions
5. **Timeout Issues**: Functions have maximum execution time limits

### Debug Mode

Enable debug mode by setting `DEBUG_MODE=True` in environment variables (not recommended for production).

### Support

- Check Vercel documentation: https://vercel.com/docs
- Review deployment logs in Vercel dashboard
- Check function logs for runtime errors

## Production Considerations

1. **Monitoring**: Set up proper monitoring and alerting
2. **Security**: Use strong secret keys and API key rotation
3. **Performance**: Monitor function execution time and memory usage
4. **Costs**: Understand Vercel pricing for your usage patterns
5. **Backups**: For real production use, implement proper data persistence

## Next Steps

After successful deployment:

1. Test all dashboard features
2. Verify analytics and charts work correctly
3. Check responsive design on different devices
4. Monitor performance and errors
5. Consider adding real data source integration for production use

Your dashboard should now be available at: `https://your-project-name.vercel.app`