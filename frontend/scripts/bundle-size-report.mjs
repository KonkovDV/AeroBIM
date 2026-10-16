/** Summarise dist/assets sizes (raw + gzip) as JSON. Usage: node scripts/bundle-size-report.mjs dist out.json */
import { readdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { gzipSync } from "node:zlib";

const [dist = "dist", out = "bundle-size.json"] = process.argv.slice(2);
const dir = path.join(dist, "assets");
const files = [];
for (const name of (await readdir(dir)).sort()) {
  const buf = await readFile(path.join(dir, name));
  files.push({ name, bytes: buf.length, gzip: gzipSync(buf).length });
}
const sum = (ext, key) => files.filter((f) => f.name.endsWith(ext)).reduce((n, f) => n + f[key], 0);
const report = {
  files,
  totals: {
    js: sum(".js", "bytes"), js_gzip: sum(".js", "gzip"),
    css: sum(".css", "bytes"), css_gzip: sum(".css", "gzip"),
    wasm: sum(".wasm", "bytes"),
    all: files.reduce((n, f) => n + f.bytes, 0),
    count: files.length,
  },
};
await writeFile(out, JSON.stringify(report, null, 2));
console.log(JSON.stringify(report.totals));
