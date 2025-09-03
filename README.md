# ApoLead Call Analytics Dashboard

A modern, responsive dashboard for visualizing call transcription analytics built with Next.js and deployed on Vercel.

## Features

- 📊 **Real-time Analytics**: Interactive charts and metrics
- 🔍 **Search & Filter**: Search transcriptions and filter by intent
- 📱 **Responsive Design**: Works on desktop and mobile
- 🚀 **Fast Loading**: Optimized for performance
- 📈 **Visual Charts**: Pie charts, line graphs, and bar charts

## Technology Stack

- **Frontend**: Next.js 14, React 18, TypeScript
- **Styling**: Bootstrap 5, Custom CSS
- **Charts**: Chart.js with React wrapper
- **Data**: CSV parsing with PapaParse
- **Deployment**: Vercel

## Quick Start

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/apolead/call_dashboard.git
cd call_dashboard
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

### Deploy to Vercel

1. Push your code to GitHub
2. Connect your GitHub repository to Vercel
3. Vercel will automatically deploy your app

Or use the Vercel CLI:
```bash
npx vercel --prod
```

## Data Format

The dashboard expects a CSV file named `call_transcriptions.csv` in the `public` directory with the following columns:

- `timestamp`: Call timestamp
- `filename`: Audio file name
- `call_date`: Date of the call
- `call_time`: Time of the call
- `phone_number`: Caller's phone number
- `call_status`: Status of the call
- `agent_name`: Name of the handling agent
- `estimated_duration_seconds`: Call duration in seconds
- `file_size`: Size of the audio file
- `duration`: Human-readable duration
- `transcription`: Full call transcription
- `summary`: AI-generated summary
- `intent`: Primary intent category
- `sub_intent`: Specific intent subcategory
- `status`: Processing status
- `processing_time`: Time taken to process
- `error_message`: Any error messages
- `primary_disposition`: Primary call disposition
- `secondary_disposition`: Secondary call disposition

## Customization

### Styling
- Modify `app/globals.css` for custom styles
- Update CSS variables in `:root` for theme colors

### Charts
- Edit chart configurations in `app/page.tsx`
- Add new chart types by importing from `react-chartjs-2`

### Data Processing
- Modify the CSV parsing logic in the `useEffect` hook
- Add new metrics calculations in the analytics section

## Environment Variables

No environment variables are required for basic operation. The app works with static CSV data.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions, please open a GitHub issue.