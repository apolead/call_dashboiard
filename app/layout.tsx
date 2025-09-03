import type { Metadata } from 'next'
import 'bootstrap/dist/css/bootstrap.min.css'
import './globals.css'

export const metadata: Metadata = {
  title: 'ApoLead Call Analytics Dashboard',
  description: 'Real-time call analytics and transcription insights',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.css" />
      </head>
      <body className="bg-light">
        <nav className="navbar navbar-expand-lg navbar-dark bg-primary">
          <div className="container-fluid">
            <span className="navbar-brand mb-0 h1">
              <i className="bi bi-graph-up me-2"></i>
              ApoLead Call Analytics
            </span>
          </div>
        </nav>
        <main>{children}</main>
      </body>
    </html>
  )
}