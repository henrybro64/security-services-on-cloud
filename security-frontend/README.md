# Security Frontend

Next.js web application for the CloudHostInspector security assessment service. Provides a modern UI for submitting security checks, viewing scan results, and managing assessment history.

## Features

- **Host Scanning**: Submit hostnames or IPs for automated security scanning
- **Manual Configuration**: Enter asset details manually (OS, ports, exposure)
- **Risk Visualization**: View security scores, issues, and recommendations
- **IP Reputation**: Display IP reputation data from AbuseIPDB
- **Recent History**: Track and view recent security assessments
- **Modern UI**: Built with Next.js 16 and Carbon Design System

## Prerequisites

- Node.js 20+
- npm or yarn
- Backend API running (local or remote)

## Local Development

### Quick Start

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   ```

3. **Open in browser:**
   Navigate to `http://localhost:3000`

### Configuration

The frontend automatically connects to `http://localhost:8000` when running locally.

To override the backend URL, create a `.env.local` file:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_KEY=your_api_key_here  # Optional
```

**Note:** Environment variables prefixed with `NEXT_PUBLIC_` are embedded at build time and exposed to the browser.

## Available Scripts

- `npm run dev` - Start development server (port 3000)
- `npm run build` - Build production bundle
- `npm run start` - Start production server (requires build first)
- `npm run lint` - Run ESLint

## Project Structure

```
security-frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx        # Root layout component
│   │   ├── page.tsx          # Main page component
│   │   └── globals.css       # Global styles
│   ├── lib/
│   │   └── api.ts            # API client functions
│   └── types/
│       └── carbon.d.ts       # Carbon Design System type definitions
├── public/                   # Static assets
├── Dockerfile                # Container image definition
├── next.config.ts            # Next.js configuration
├── package.json              # Dependencies and scripts
└── README.md                 # This file
```

## Building for Production

### Local Build

```bash
npm run build
npm run start
```

### Docker Build

The Dockerfile uses a multi-stage build for optimal image size:

```bash
docker build -t security-frontend:latest \
  --build-arg NEXT_PUBLIC_API_BASE_URL=https://your-backend-url.com \
  .
```

**Important:** The `NEXT_PUBLIC_API_BASE_URL` must be provided at build time as it's embedded in the JavaScript bundle.

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `NEXT_PUBLIC_API_BASE_URL` | Backend API base URL | `http://localhost:8000` | No |
| `NEXT_PUBLIC_API_KEY` | API key for backend authentication | - | No |

### Build-Time vs Runtime

- **Build-time**: `NEXT_PUBLIC_API_BASE_URL` must be set during `npm run build` or Docker build
- **Runtime**: Cannot be changed after build (embedded in JavaScript bundle)

For Azure deployment, the backend URL is passed as a build argument in the GitHub Actions workflow.

## Usage

### Host Scanning

1. Enter a hostname or IP address (e.g., `scanme.nmap.org`)
2. Optionally check "Scan public IP" if the target is publicly accessible
3. Click "Scan Host"
4. View results including detected OS, open ports, and risk assessment

### Manual Configuration

1. Select operating system (e.g., Ubuntu, Windows)
2. Check "Public IP" if the asset is internet-facing
3. Enter ports in format: `port/protocol/exposure`
   - Example: `22/tcp/public` (SSH on port 22, TCP, exposed to internet)
   - Example: `443/tcp/public` (HTTPS on port 443, TCP, exposed to internet)
   - Example: `3306/tcp/private` (MySQL on port 3306, TCP, internal only)
4. Click "Check Security"
5. Review risk score, issues, and recommendations

### Viewing Results

- **Risk Score**: 0-100 (higher is better)
- **Issues**: List of security concerns detected
- **Recommendations**: Suggested remediation steps
- **IP Reputation**: AbuseIPDB data (if available)
- **Recent History**: Access previous assessments from the sidebar

## API Integration

The frontend communicates with the backend via REST API:

- `POST /check` - Submit manual security check
- `POST /scan` - Submit host scan request
- `GET /check/{request_id}` - Retrieve cached result

See `src/lib/api.ts` for API client implementation.

## Styling

The application uses:
- **Carbon Design System**: IBM's open-source design system
- **Sass**: For CSS preprocessing
- **Tailwind CSS**: Utility-first CSS framework

## Deployment

### Azure Container Apps

The frontend is deployed to Azure Container Apps via Terraform and GitHub Actions.

1. **Infrastructure**: Terraform creates the Container App with placeholder image
2. **CI/CD**: GitHub Actions builds the Docker image with the correct `NEXT_PUBLIC_API_BASE_URL`
3. **Update**: GitHub Actions pushes to ACR and updates the Container App

### Build Configuration

The GitHub Actions workflow:
1. Sets up Docker Buildx for efficient builds
2. Builds the image with `NEXT_PUBLIC_API_BASE_URL` from GitHub secrets
3. Pushes to Azure Container Registry
4. Updates the Container App with the new image

**Important:** After deploying infrastructure, update the `NEXT_PUBLIC_API_BASE_URL` GitHub secret with the backend URL, then re-run the frontend workflow.

## Troubleshooting

### "Failed to fetch" Error

- Verify backend is running and accessible
- Check `NEXT_PUBLIC_API_BASE_URL` is correct
- Verify CORS is configured on backend to allow frontend origin
- Check browser console for detailed error messages

### Build Errors

- Ensure Node.js version matches `.nvmrc` (if present) or package.json requirements
- Clear `.next` directory and `node_modules`, then reinstall:
  ```bash
  rm -rf .next node_modules
  npm install
  ```

### Backend URL Not Updating

The `NEXT_PUBLIC_API_BASE_URL` is embedded at build time. To change it:
1. Update the environment variable or build argument
2. Rebuild the application
3. Redeploy

### Docker Build Fails

- Verify `NEXT_PUBLIC_API_BASE_URL` is provided as build argument
- Check Docker has sufficient memory (Next.js builds can be memory-intensive)
- Review Docker logs for specific error messages

## Development Tips

- Use browser DevTools to inspect API requests
- Check Network tab for failed requests
- Review backend logs for server-side errors
- Use React DevTools for component debugging
