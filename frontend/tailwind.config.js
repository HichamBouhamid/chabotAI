/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,js,jsx}"],
  theme: {
    extend: {
      screens:{
        "chatpdf-bp": "755px",
      }
    },
  },
  plugins: [],
}