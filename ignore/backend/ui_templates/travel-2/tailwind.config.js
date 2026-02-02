/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        "color-background-brand-default": "var(--color-background-brand-default)",
        "color-background-default-default": "var(--color-background-default-default)",
        "color-background-default-secondary": "var(--color-background-default-secondary)",
        "color-border-default-default": "var(--color-border-default-default)",
        "color-primitives-brand-800": "var(--color-primitives-brand-800)",
        "color-primitives-gray-100": "var(--color-primitives-gray-100)",
        "color-primitives-gray-300": "var(--color-primitives-gray-300)",
        "color-primitives-gray-400": "var(--color-primitives-gray-400)",
        "color-text-brand-on-brand": "var(--color-text-brand-on-brand)",
        "color-text-default-default": "var(--color-text-default-default)",
        "color-text-default-secondary": "var(--color-text-default-secondary)",
        "color-text-disabled-default": "var(--color-text-disabled-default)",
        "color-text-on-surface": "var(--color-text-on-surface)",
        "m3-schemes-surface-container-high": "var(--m3-schemes-surface-container-high)",
      },
      fontFamily: {
        "body-base": "var(--body-base-font-family)",
        "body-small": "var(--body-small-font-family)",
        "body-strong": "var(--body-strong-font-family)",
        "m3-body-large": "var(--m3-body-large-font-family)",
        "single-line-body-base": "var(--single-line-body-base-font-family)",
        "text-extra-small": "var(--text-extra-small-font-family)",
      },
      boxShadow: {
        "drop-shadow-300": "var(--drop-shadow-300)",
      },
    },
  },
  plugins: [],
};