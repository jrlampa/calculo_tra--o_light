/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Calibri', 'Arial', 'sans-serif'],
      },
      colors: {
        'tracao-orange': '#E07820',
        'tracao-red': '#C00000',
        'tracao-blue': '#4472C4',
        'tracao-green': '#538135',
        'tracao-dark': '#1F1F1F',
      },
    },
  },
  plugins: [],
}
