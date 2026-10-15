// Repeatable acceptance test: real browser (iPhone 14 WebKit) walks the whole flow against a running app.
// Usage: cd frontend && npm run e2e [-- baseUrl]   Needs backend + frontend running (and Ollama, or DEMO_MODE=true).
import { webkit, devices } from "playwright";
import { fileURLToPath } from "node:url";
import path from "node:path";

const base = process.argv[2] ?? "http://localhost:3000";
const fixture = path.join(path.dirname(fileURLToPath(import.meta.url)), "fixtures", "product.png");
const browser = await webkit.launch();
const page = await (await browser.newContext({ ...devices["iPhone 14"] })).newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
const step = (m) => console.log("•", m);
const fail = async (m) => { console.error("FAIL:", m); await page.screenshot({ path: "e2e-failure.png" }).catch(() => {}); await browser.close(); process.exit(1); };

await page.goto(`${base}/create`, { waitUntil: "load" });
step("upload photo");
await page.getByLabel("Choose product photo").setInputFiles(fixture);
await page.getByAltText("Your product photo").waitFor({ timeout: 20000 });
step("fill facts");
await page.getByPlaceholder("e.g. Silver moon necklace").fill("Hide and seek biscuit");
await page.getByLabel(/Main features/).fill("Triangle shaped\nCrunchy biscuit with choco chips");
await page.getByRole("button", { name: /Next: choose style/ }).click();
await page.getByRole("radio", { name: "Playful" }).click();
await page.getByRole("radio", { name: "Warm & cozy" }).click();
step("generate");
await page.getByRole("button", { name: /^Generate$/ }).click();
await page.waitForURL(/\/jobs\//, { timeout: 15000 });
step("wait for copy");
await page.getByText(/Written by|Demo Mode/).first().waitFor({ timeout: 180000 }).catch(() => fail("copy never appeared"));
step("edit + copy a field");
const title = page.getByRole("textbox", { name: "Product title" });
await title.fill("Hide & Seek Biscuit (edited)");
await title.blur();
step("open video tab, wait for video");
await page.getByRole("tab", { name: "Video" }).click();
await page.locator("video").waitFor({ timeout: 120000 }).catch(() => fail("video never appeared"));
const meta = await page.evaluate(() => new Promise((res) => {
  const v = document.querySelector("video"); if (v.readyState >= 1) return res({ d: v.duration, w: v.videoWidth, h: v.videoHeight });
  v.addEventListener("loadedmetadata", () => res({ d: v.duration, w: v.videoWidth, h: v.videoHeight })); setTimeout(() => res(null), 15000);
}));
if (!meta || Math.abs(meta.d - 10) > 0.6 || meta.h <= meta.w) await fail(`bad video metadata ${JSON.stringify(meta)}`);
if (!(await page.getByText(/Animated-photo ad/).isVisible())) await fail("method label missing");
if (errors.length) await fail("page errors: " + errors.join(" | "));
await page.screenshot({ path: "e2e-result.png", fullPage: false });
console.log("PASS", JSON.stringify(meta));
await browser.close();
