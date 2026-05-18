import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      colors: {
        ink: '#172033',
        panel: '#f7f8fb',
      },
    },
  },
  plugins: [],
} satisfies Config

