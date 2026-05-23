import { existsSync, readdirSync, statSync } from "fs";
import { resolve } from "path";

const dist = resolve(process.cwd(), "dist");

const requiredFiles = [
  "manifest.json",
  "background.js",
  "content_extractor.js",
  "dashboard.html",
  "newtab.html",
];

const missing = requiredFiles.filter((file) => !existsSync(resolve(dist, file)));

const assetsDir = resolve(dist, "assets");
const hasAssets = existsSync(assetsDir) && statSync(assetsDir).isDirectory() && readdirSync(assetsDir).length > 0;

if (missing.length > 0 || !hasAssets) {
  if (missing.length > 0) {
    console.error("Missing required dist files:", missing.join(", "));
  }
  if (!hasAssets) {
    console.error("Missing or empty dist/assets directory");
  }
  process.exit(1);
}

console.log("Build validation passed: required extension files are present in dist/.");
