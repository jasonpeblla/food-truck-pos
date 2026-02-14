/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'truck-orange': '#ff6b35',
        'truck-yellow': '#ffc233',
        'truck-green': '#2ecc71',
        'truck-red': '#e74c3c',
      }
    },
  },
  plugins: [],
}
