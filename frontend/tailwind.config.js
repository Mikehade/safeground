/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        safe: { 50: '#ecfdf5', 500: '#22c55e', 700: '#15803d' },
        warn: { 50: '#fffbeb', 500: '#f59e0b', 700: '#b45309' },
        danger: { 50: '#fef2f2', 500: '#ef4444', 700: '#b91c1c' },
        ground: { 50: '#f8f7f4', 100: '#edecea', 200: '#d8d5cf', 800: '#2d2a24', 900: '#1a1815' },
      },
      fontFamily: {
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
        display: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
