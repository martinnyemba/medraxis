import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: globals.browser,
    },
    rules: {
      // Context providers intentionally co-locate their hook (useAuth, useTenant,
      // useToast) with the component; the Fast-Refresh-only rule misfires here.
      'react-refresh/only-export-components': 'off',
      // Syncing an async-loaded default (e.g. the first facility) into state is a
      // legitimate effect; surface it as guidance, not a build-breaking error.
      'react-hooks/set-state-in-effect': 'warn',
    },
  },
])
