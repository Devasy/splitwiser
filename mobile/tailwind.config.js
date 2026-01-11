/** @type {import('tailwindcss').Config} */
module.exports = {
  // NOTE: Update this to include the paths to all of your component files.
  content: ["./app/**/*.{js,jsx,ts,tsx}", "./components/**/*.{js,jsx,ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter_400Regular', 'sans-serif'],
        mono: ['SpaceGrotesk_400Regular', 'monospace'],
        'sans-bold': ['Inter_700Bold', 'sans-serif'],
        'mono-bold': ['SpaceGrotesk_700Bold', 'monospace'],
      },
      colors: {
        neo: {
          main: '#8855ff',
          second: '#ff9900',
          accent: '#00cc88',
          bg: '#f0f0f0',
          dark: '#1a1a1a',
          white: '#ffffff',
        }
      },
      boxShadow: {
        'neo': '4px 4px 0px 0px #1a1a1a',
        'neo-sm': '2px 2px 0px 0px #1a1a1a',
        'neo-lg': '6px 6px 0px 0px #1a1a1a',
      }
    },
  },
  plugins: [],
}
