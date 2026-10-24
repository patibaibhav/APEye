/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: '#0f0f12',
          secondary: '#151519',
          tertiary: '#1b1b22',
        },
        card: {
          DEFAULT: '#16161b',
          hover: '#1e1e25',
          border: '#272730',
        },
        matte: {
          50: '#f9f9fb',
          100: '#f1f1f4',
          200: '#e4e4e9',
          300: '#d1d1d8',
          400: '#9e9ea9',
          500: '#71717f',
          600: '#52525e',
          700: '#383842',
          800: '#23232a',
          900: '#141419',
          950: '#0c0c0f',
        },
        pastel: {
          rose: {
            DEFAULT: '#f87171',
            light: '#fca5a5',
            bg: 'rgba(248, 113, 113, 0.12)',
            border: 'rgba(248, 113, 113, 0.25)',
          },
          amber: {
            DEFAULT: '#fbbf24',
            light: '#fcd34d',
            bg: 'rgba(251, 191, 36, 0.12)',
            border: 'rgba(251, 191, 36, 0.25)',
          },
          mint: {
            DEFAULT: '#4ade80',
            light: '#86efac',
            bg: 'rgba(74, 222, 128, 0.12)',
            border: 'rgba(74, 222, 128, 0.25)',
          },
          lavender: {
            DEFAULT: '#b4a2f8',
            light: '#c4b5fd',
            bg: 'rgba(180, 162, 248, 0.12)',
            border: 'rgba(180, 162, 248, 0.25)',
          },
          slate: {
            DEFAULT: '#94a3b8',
            light: '#cbd5e1',
            bg: 'rgba(148, 163, 184, 0.12)',
            border: 'rgba(148, 163, 184, 0.25)',
          },
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Menlo', 'Monaco', 'Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
}
