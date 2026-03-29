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
      fontWeight: {
        regular:  '400',
        semibold: '600',
        bold:     '700',
      },
      lineHeight: {
        tight:  '1.2',
        snug:   '1.3',
        normal: '1.4',
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
          // Focus ring used for box-shadow glow (rgba counterpart of focus border)
          'focus-ring': 'rgba(46, 105, 196, 0.35)',
        },
        'tracao-orange': '#E07820',
        'tracao-red': '#C00000',
        'tracao-blue': '#4472C4',
        'tracao-green': '#538135',
        'tracao-dark': '#1F1F1F',
        result: {
          ok:                '#538135',
          'ok-bg':           '#ecf8ec',
          tolerancia:        '#E07820',
          'tolerancia-bg':   '#fff4e8',
          error:             '#C00000',
          'error-bg':        '#ffecec',
        },
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
      transitionDuration: {
        fast: '160ms',
        base: '200ms',
        slow: '280ms',
      },
      transitionTimingFunction: {
        'snappy': 'cubic-bezier(0.3, 0, 0.1, 1)',
        'ease-out-smooth': 'cubic-bezier(0, 0, 0.2, 1)',
      },
      fontSize: {
        'calc-result':   ['14px', { lineHeight: '1.4', fontWeight: '700' }],
        'calc-label':    ['12px', { lineHeight: '1.3', fontWeight: '600' }],
        'calc-field':    ['10px', { lineHeight: '1.2', fontWeight: '400' }],
        'calc-table':    ['9px',  { lineHeight: '1.2', fontWeight: '400' }],
      },
      // ─── Motion tokens ─────────────────────────────────────────────────────
      // These mirror the keyframes already defined in src/index.css so they are
      // also usable as Tailwind utility classes (animate-persist-pulse, etc.)
      animation: {
        'persist-pulse':  'persist-pulse 1s ease-in-out infinite',
        'glass-fade-up':  'glass-fade-up 280ms cubic-bezier(0,0,0.2,1) both',
        'undo-toast-in':  'undo-toast-in 0.18s ease-out',
        'spin':           'spin 1s linear infinite',
      },
      keyframes: {
        'persist-pulse': {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0.7' },
        },
        'glass-fade-up': {
          from: { opacity: '0', transform: 'translateY(4px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        'undo-toast-in': {
          from: { opacity: '0', transform: 'translateX(-50%) translateY(12px)' },
          to:   { opacity: '1', transform: 'translateX(-50%) translateY(0)' },
        },
        spin: {
          from: { transform: 'rotate(0deg)' },
          to:   { transform: 'rotate(360deg)' },
        },
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
