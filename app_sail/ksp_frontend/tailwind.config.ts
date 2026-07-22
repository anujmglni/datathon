import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        police: {
          dark: "#0b132b",
          card: "#1c2541",
          border: "#3a506b",
          accent: "#48cae4",
          gold: "#f77f00",
          success: "#10b981",
          error: "#ef4444",
        },
      },
    },
  },
  plugins: [],
};
export default config;
