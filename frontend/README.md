# Next.js Frontend - Quick Start

## Installation

```bash
cd frontend
npm install
```

## Development

```bash
# Start Next.js development server
npm run dev
```

The application will be available at: http://localhost:3000

## Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/
│   ├── components/          # React components
│   │   ├── ECommerceApp.tsx # Main app component
│   │   ├── ui/              # Reusable UI components
│   │   └── ...
│   ├── lib/                 # API client and utilities
│   ├── types/               # TypeScript type definitions
│   ├── layout.tsx           # Root layout
│   ├── page.tsx             # Home page
│   └── globals.css          # Global styles
├── public/                  # Static assets
├── next.config.ts           # Next.js configuration
├── tailwind.config.js       # Tailwind CSS configuration
└── package.json             # Dependencies
```

## Key Features

- **Next.js 14** with App Router
- **React 18** with Server Components
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **Zustand** for state management
- **Axios** for API calls

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript compiler
- `npm run format` - Format code with Prettier

## Environment Variables

Create a `.env.local` file:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Notes

- All components with client-side features (hooks, event handlers) use `'use client'` directive
- API routes are proxied through Next.js for CORS handling
- Images are optimized using Next.js Image component
- The app uses Next.js App Router (not Pages Router)
