/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: { brand: { 50: '#fff7ed', 500: '#f97316', 900: '#7c2d12' } },
      backdropBlur: { xs: '2px' },
      animation: { float: 'float 6s ease-in-out infinite', glow: 'glow 2s ease-in-out infinite alternate' },
      keyframes: {
        float: { '0%, 100%': { transform: 'translateY(0px)' }, '50%': { transform: 'translateY(-10px)' } },
        glow: { '0%': { boxShadow: '0 0 5px rgba(249,115,22,0.2)' }, '100%': { boxShadow: '0 0 20px rgba(249,115,22,0.4)' } },
      },
    },
  },
  plugins: [],
}
