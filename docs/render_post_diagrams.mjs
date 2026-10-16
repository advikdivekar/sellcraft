// Renders docs/images/post/*.svg to 2x PNGs (needs playwright from frontend/node_modules).  node docs/render_post_diagrams.mjs
import { webkit } from "../frontend/node_modules/playwright/index.mjs";
import { readdirSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
const dir = resolve(dirname(fileURLToPath(import.meta.url)), "images/post");
const b = await webkit.launch(); const ctx = await b.newContext({ viewport: { width: 860, height: 1400 }, deviceScaleFactor: 2 }); const p = await ctx.newPage();
for (const f of readdirSync(dir).filter((x) => x.endsWith(".svg"))) {
  await p.goto("file://" + resolve(dir, f)); await p.waitForTimeout(120);
  await (await p.$("svg")).screenshot({ path: resolve(dir, f.replace(".svg", ".png")) });
}
await b.close();
