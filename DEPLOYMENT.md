# Deployment Guide

## Deploy to Vercel (Recommended)

### Method 1: GitHub Integration

1. **Push to GitHub** (already done):
   ```bash
   git push origin master
   ```

2. **Connect to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Sign up/login with your GitHub account
   - Click "Add New Project"
   - Import `apolead/call_dashboiard` repository
   - Configure project settings:
     - Framework Preset: Next.js
     - Build Command: `npm run build`
     - Output Directory: `.next`
   - Click "Deploy"

3. **Your app will be live** at: `https://call-dashboiard.vercel.app`

### Method 2: Vercel CLI

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy from local directory**:
   ```bash
   cd call_dashboard
   vercel --prod
   ```

## Environment Setup

### Development
```bash
npm install
npm run dev
```
Open http://localhost:3000

### Production Build (Local Testing)
```bash
npm run build
npm start
```

## CSV Data Update

To update the dashboard data:

1. **Replace CSV file**:
   - Update `public/call_transcriptions.csv` with new data
   - Ensure column names match the expected format

2. **Redeploy**:
   ```bash
   git add public/call_transcriptions.csv
   git commit -m "Update call data"
   git push origin master
   ```
   Vercel will automatically redeploy with new data.

## Custom Domain (Optional)

1. In Vercel dashboard, go to your project
2. Navigate to "Settings" > "Domains"
3. Add your custom domain
4. Configure DNS records as instructed

## Performance Optimization

The dashboard is optimized for:
- ✅ Fast loading with static generation
- ✅ Efficient CSV parsing
- ✅ Responsive charts
- ✅ Mobile-friendly design
- ✅ SEO-friendly structure

## Troubleshooting

### Build Errors
- Ensure all dependencies are in `package.json`
- Check TypeScript errors: `npm run lint`
- Verify CSV format matches expected columns

### Data Issues
- Check CSV file is in `public/` directory
- Verify CSV has proper headers
- Ensure no malformed data rows

### Performance Issues
- Large CSV files (>1MB) may slow loading
- Consider data pagination for large datasets
- Use CSV compression if needed