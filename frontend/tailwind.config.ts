import type { Config } from 'tailwindcss';

import forms from '@tailwindcss/forms';

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: '#1F2A4A',
          50: '#F0F2F7',
          100: '#E1E5EF',
          200: '#C3CBDF',
          300: '#A4B2CF',
          400: '#8698BF',
          500: '#687EAF',
          600: '#4D6291',
          700: '#3A496D',
          800: '#273149',
          900: '#1F2A4A',
        },
        gold: {
          DEFAULT: '#B8973A',
          50: '#F9F7F1',
          100: '#F4EEE3',
          200: '#E8DCC7',
          300: '#DDCAAB',
          400: '#D1B98F',
          500: '#C6A773',
          600: '#B8973A',
          700: '#8A712C',
          800: '#5C4B1D',
          900: '#2E260F',
        }
      }
    },
  },
  plugins: [forms],
} satisfies Config;
