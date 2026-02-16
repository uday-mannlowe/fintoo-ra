/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Cormorant Garamond"', 'serif'],
        sans:    ['Sora', 'sans-serif'],
      },
      colors: {
        gold:  '#c9a84c',
        ink:   '#0d0d0d',
        paper: '#f5f0e8',
        cream: '#ede8dc',
      },
      animation: {
        'fade-up': 'fadeUp 0.5s ease forwards',
      },
    },
  },
  plugins: [],
}
