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
        surface: {
          glass: 'rgba(255, 255, 255, 0.72)',
          'glass-strong': 'rgba(255, 255, 255, 0.84)',
          input: 'rgba(245, 249, 255, 0.88)',
          readonly: 'rgba(233, 240, 250, 0.95)',
          panel: '#ffffff',
        },
        status: {
          loading: '#fff4e8',
          success: '#ecf8ec',
          error: '#ffecec',
          'loading-text': '#7f4b0f',
          'success-text': '#24613a',
          'error-text': '#7f1f1f',
        },
        action: {
          primary: '#3b66ad',
          'primary-hover': '#315998',
          secondary: '#bc5a17',
          'secondary-hover': '#a84b11',
        },
        border: {
          soft: 'rgba(132, 154, 188, 0.46)',
          strong: 'rgba(112, 137, 176, 0.62)',
          focus: '#2f66c1',
        },
        'tracao-orange': '#E07820',
        'tracao-red': '#C00000',
        'tracao-blue': '#4472C4',
        'tracao-green': '#538135',
        'tracao-dark': '#1F1F1F',
      },
      boxShadow: {
        glass: '0 10px 28px rgba(23, 46, 90, 0.14)',
        'glass-soft': '0 4px 14px rgba(34, 57, 96, 0.1)',
        action: '0 7px 16px rgba(52, 84, 139, 0.24)',
      },
      borderRadius: {
        panel: '10px',
        card: '12px',
        soft: '8px',
      },
    },
  },
  plugins: [
    function({ addUtilities }) {
      addUtilities({
        '.pb-safe': {
          '@supports (padding: max(0px))': {
            paddingBottom: 'max(0.75rem, env(safe-area-inset-bottom))',
          },
          '@supports not (padding: max(0px))': {
            paddingBottom: '0.75rem',
          },
        },
        '.pt-safe': {
          '@supports (padding: max(0px))': {
            paddingTop: 'max(0.75rem, env(safe-area-inset-top))',
          },
          '@supports not (padding: max(0px))': {
            paddingTop: '0.75rem',
          },
        },
        '.pl-safe': {
          '@supports (padding: max(0px))': {
            paddingLeft: 'max(0.75rem, env(safe-area-inset-left))',
          },
          '@supports not (padding: max(0px))': {
            paddingLeft: '0.75rem',
          },
        },
        '.pr-safe': {
          '@supports (padding: max(0px))': {
            paddingRight: 'max(0.75rem, env(safe-area-inset-right))',
          },
          '@supports not (padding: max(0px))': {
            paddingRight: '0.75rem',
          },
        },
      })
    },
  ],
}
