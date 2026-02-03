import react from "@vitejs/plugin-react";
import tailwind from "tailwindcss";
import { defineConfig, Plugin } from "vite";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const plugins: (Plugin | Plugin[])[] = [react()];

  return {
    plugins,
    base: "./",
    css: {
      postcss: {
        plugins: [tailwind()],
      },
    },
    build: {
      target: 'esnext',
      outDir: resolve(__dirname, "dist"),
      rollupOptions: {
        input: {
          newtab: resolve(__dirname, "newtab.html"),
          background: resolve(__dirname, "background.js"),
        },
        output: {
          entryFileNames: "[name].js",
          chunkFileNames: "[name].js",
          assetFileNames: "[name].[ext]",
        },
      },
    },
  };
});
