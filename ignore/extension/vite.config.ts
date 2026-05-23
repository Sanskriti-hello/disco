import react from "@vitejs/plugin-react";
import tailwind from "tailwindcss";
import { defineConfig, Plugin } from "vite";
import { resolve, dirname, join } from "path";
import { fileURLToPath } from "url";
import { cpSync, existsSync } from "fs";

const __dirname = dirname(fileURLToPath(import.meta.url));

function copyExtensionRuntimeFiles(): Plugin {
  return {
    name: "copy-extension-runtime-files",
    closeBundle() {
      const distDir = resolve(__dirname, "dist");
      const staticFiles = ["manifest.json", "content_extractor.js"];

      for (const file of staticFiles) {
        const src = resolve(__dirname, file);
        if (existsSync(src)) {
          cpSync(src, join(distDir, file));
        }
      }

      const iconsSrc = resolve(__dirname, "icons");
      const iconsDest = join(distDir, "icons");
      if (existsSync(iconsSrc)) {
        cpSync(iconsSrc, iconsDest, { recursive: true });
      }
    },
  };
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const plugins: (Plugin | Plugin[])[] = [react(), copyExtensionRuntimeFiles()];

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
          dashboard: resolve(__dirname, "dashboard.html"),
          background: resolve(__dirname, "background.js"),
        },
        output: {
          entryFileNames: "[name].js",
          chunkFileNames: "[name].js",
          assetFileNames: "assets/[name].[ext]",
        },
      },
    },
  };
});
