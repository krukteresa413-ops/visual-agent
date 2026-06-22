/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: { 50: '#fff7ed', 500: '#f97316', 900: '#7c2d12' },
        lo: {
          title: '#2F3640',
          canvas: '#F5F5F5',
          float: '#FFFFFF',
          description: '#4A535F',
          tab: '#F1F3F5',
          selected: '#E5E6EC',
        },
      },
      backdropBlur: { xs: '2px' },
      boxShadow: { 'lo-elevation-100': '0 2px 8px rgba(0,0,0,.15)' },
      borderRadius: { lo: '14px' },
      animation: { float: 'float 6s ease-in-out infinite', glow: 'glow 2s ease-in-out infinite alternate' },
      keyframes: {
        float: { '0%, 100%': { transform: 'translateY(0px)' }, '50%': { transform: 'translateY(-10px)' } },
        glow: { '0%': { boxShadow: '0 0 5px rgba(249,115,22,0.2)' }, '100%': { boxShadow: '0 0 20px rgba(249,115,22,0.4)' } },
      },
    },
  },
  plugins: [],
}
