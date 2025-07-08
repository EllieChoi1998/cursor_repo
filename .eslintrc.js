module.exports = {
  root: true,
  env: {
    node: true,
    browser: true,
    es2021: true
  },
  extends: [
    'plugin:vue/vue3-essential',
    '@vue/standard'
  ],
  parserOptions: {
    ecmaVersion: 2021,
    sourceType: 'module'
  },
  rules: {
    'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'vue/multi-word-component-names': 'off',
    'comma-dangle': 'off',
    'semi': 'off',
    'quotes': 'off',
    'indent': 'off',
    'space-before-function-paren': 'off',
    'object-curly-spacing': 'off',
    'array-bracket-spacing': 'off'
  }
} 