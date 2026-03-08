/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        studio: {
          bg: '#0d0d0d',
          panel: '#1a1a1a',
          border: '#2a2a2a',
          accent: '#7c3aed',
          'accent-hover': '#6d28d9',
        },
      },
    },
  },
  plugins: [],
}
