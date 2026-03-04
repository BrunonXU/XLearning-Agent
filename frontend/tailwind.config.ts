import type { Config } from 'tailwindcss'
import typography from '@tailwindcss/typography'

const config: Config = {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: '#FFFFFF',
          secondary: '#F8F9FA',
          tertiary: '#F1F3F4',
        },
        primary: {
          DEFAULT: '#1A73E8',
          hover: '#1557B0',
          light: '#E8F0FE',
        },
        accent: {
          DEFAULT: '#F97316',
          light: '#FFF7ED',
        },
        text: {
          primary: '#202124',
          secondary: '#5F6368',
          disabled: '#9AA0A6',
        },
        border: {
          DEFAULT: '#DADCE0',
          focus: '#1A73E8',
        },
        dark: {
          bg: '#1C1C1E',
          surface: '#2C2C2E',
          text: '#F5F5F7',
          border: '#3A3A3C',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      fontSize: {
        xs:   ['12px', { lineHeight: '16px' }],
        sm:   ['13px', { lineHeight: '20px' }],
        base: ['14px', { lineHeight: '22px' }],
        md:   ['15px', { lineHeight: '24px' }],
        lg:   ['16px', { lineHeight: '24px' }],
        xl:   ['18px', { lineHeight: '28px' }],
      },
      borderRadius: {
        lg: '8px',
        xl: '12px',
        '2xl': '16px',
      },
      transitionDuration: {
        DEFAULT: '150ms',
      },
    },
  },
  plugins: [typography],
}

export default config
