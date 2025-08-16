import type { Config } from 'tailwindcss'

export default {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        // App tokens for UI components
        primary: {
          DEFAULT: '#6366f1', // indigo-500
        },
        accent: {
          DEFAULT: '#8b5cf6', // violet-500
        },
        muted: {
          DEFAULT: '#94a3b8', // slate-400
        },
        'muted-foreground': '#94a3b8',
        destructive: {
          DEFAULT: '#ef4444', // red-500
        },
        border: '#ffffff1a', // white/10
        cream: {
          50: '#faf7f2',
          100: '#f5efe3',
          200: '#eee3cf',
          300: '#e5d4b6',
        },
        beige: {
          200: '#d9cbb6',
          300: '#cbb69b',
          400: '#bfa17d',
        },
        brown: {
          500: '#7a5c3a',
          600: '#634a2f',
          700: '#4e3a25'
        }
      },
      fontFamily: {
        sans: [
          'Inter', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'Noto Sans', 'sans-serif'
        ]
      },
      boxShadow: {
        card: '0 6px 16px rgba(0,0,0,0.08)'
      }
    }
  },
  plugins: []
} satisfies Config
