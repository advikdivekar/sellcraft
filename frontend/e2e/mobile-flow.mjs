// Repeatable acceptance test: a real browser (iPhone 14 WebKit) walks the whole flow against a running app.
// Usage: cd frontend && npm run e2e [-- baseUrl]   Needs backend + frontend running (and Ollama, or DEMO_MODE=true).
import { webkit, devices } from "playwright";
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const base = process.argv[2] ?? "http://localhost:3000";
const dir = path.join(path.dirname(fileURLToPath(import.meta.url)), "fixtures");
const fixtures = [path.join(dir, "product.png"), path.join(dir, "product2.png")];
// dev-phone.sh protects the app with a random access code; pick it up automatically.
const codeFile = path.join(process.env.TMPDIR ?? "/tmp", "sellcraft-dev", "access_code");
const accessCode = process.env.ACCESS_CODE ?? (fs.existsSync(codeFile) ? fs.readFileSync(codeFile, "utf8").trim() : "");

const browser = await webkit.launch();
const page = await (await browser.newContext({ ...devices["iPhone 14"] })).newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
const step = (m) => console.log("•", m);
const fail = async (m) => { console.error("FAIL:", m); await page.screenshot({ path: "e2e-failure.png" }).catch(() => {}); await browser.close(); process.exit(1); };

await page.goto(`${base}/${accessCode ? `#k=${accessCode}` : ""}`, { waitUntil: "load" });
step("home page");
await page.getByRole("link", { name: /Create your first kit/ }).first().click();
await page.getByRole("heading", { name: "Create a marketing kit" }).waitFor({ timeout: 20000 });

step("photos step: upload two photos");
await page.getByLabel("Choose product photos").setInputFiles(fixtures);
await page.getByAltText("Product photo 2").waitFor({ timeout: 30000 });
step("photo is read by the vision model");
await page.getByText(/Reading your photos/).waitFor({ state: "hidden", timeout: 120000 }).catch(() => fail("photo scan never finished"));
if (!(await page.getByText(/pre-filled \d+ field|couldn't read anything/).first().isVisible())) await fail("no scan result banner");
await page.getByRole("button", { name: "Next" }).click();

step("facts step");
await page.getByPlaceholder("e.g. Silver moon necklace").fill("Hide and seek biscuit");
const more = page.getByRole("button", { name: /More details/ });
if ((await more.getAttribute("aria-expanded")) !== "true") await more.click();
await page.getByLabel(/Main features/).fill("Triangle shaped\nCrunchy biscuit with choco chips");
await page.getByLabel(/Verified benefits/).fill("Crunchy texture\nChoco chips in every bite");
await page.getByRole("button", { name: "Next" }).click();

step("style step");
await page.getByRole("radio", { name: "Playful" }).click();
await page.getByRole("radio", { name: /Warm, soft|Warm & cozy/ }).click();
step("generate");
await page.getByRole("button", { name: "Generate kit" }).last().click();
await page.waitForURL(/\/jobs\//, { timeout: 15000 });

const t0 = Date.now();
step("progress bar is shown and advances");
await page.getByRole("progressbar").waitFor({ timeout: 20000 }).catch(() => fail("no progress bar"));
const p1 = Number(await page.getByRole("progressbar").getAttribute("aria-valuenow"));
await page.waitForTimeout(10000);
const bar = page.getByRole("progressbar");
const p2 = (await bar.count()) ? Number(await bar.getAttribute("aria-valuenow")) : 100;
console.log(`  progress ${p1}% -> ${p2}%`);
if (!(p2 > p1)) await fail(`progress did not advance (${p1} -> ${p2})`);

step("wait for the kit to finish");
await page.getByText("All changes saved").waitFor({ state: "hidden", timeout: 1000 }).catch(() => {});
await page.getByRole("button", { name: "Share" }).first().waitFor({ timeout: 240000 }).catch(() => fail("kit never finished"));
console.log(`  kit ready after ${Math.round((Date.now() - t0) / 1000)}s`);

step("overview: video + deck");
await page.locator("video").waitFor({ timeout: 60000 }).catch(() => fail("video never appeared"));
const meta = await page.evaluate(() => new Promise((res) => {
  const v = document.querySelector("video"); if (v.readyState >= 1) return res({ d: v.duration, w: v.videoWidth, h: v.videoHeight });
  v.addEventListener("loadedmetadata", () => res({ d: v.duration, w: v.videoWidth, h: v.videoHeight })); setTimeout(() => res(null), 15000);
}));
if (!meta || Math.abs(meta.d - 10) > 0.6 || meta.h <= meta.w) await fail(`bad video metadata ${JSON.stringify(meta)}`);
await page.getByLabel("Image deck slides").waitFor({ timeout: 30000 }).catch(() => fail("deck carousel missing"));
const slides = await page.getByLabel("Image deck slides").locator("img").count();
console.log(`  video ${JSON.stringify(meta)}, deck slides: ${slides}`);
if (slides < 3) await fail(`expected a deck of at least 3 slides, got ${slides}`);
const kinds = await page.getByLabel("Image deck slides").locator("img").evaluateAll((els) => els.map((e) => e.alt));
console.log("  ", kinds.join(" | "));
if (!kinds.some((k) => /Benefits/.test(k))) await fail("benefits slide missing although two benefits were given");

step("copy tab: edit a field");
await page.getByRole("tab", { name: "Copy" }).click();
const title = page.getByRole("textbox", { name: "Product title" });
await title.fill("Hide & Seek Biscuit (edited)");
await title.blur();
await page.getByText("All changes saved").waitFor({ timeout: 15000 }).catch(() => fail("edit was not saved"));

step("photos tab");
await page.getByRole("tab", { name: /Photos/ }).click();
const groups = await page.getByRole("heading", { name: /Studio photos|White background|Transparent cut-outs/ }).count();
console.log(`  ${groups} photo groups`);
if (groups < 2) await fail("expected studio + white-background photo groups");

step("share tab");
await page.getByRole("tab", { name: "Share" }).click();
if (!(await page.getByRole("link", { name: /Download kit/ }).first().isVisible())) await fail("kit download missing");
if (!(await page.getByRole("button", { name: /Copy post/ }).first().isVisible())) await fail("copy post missing");

step("connections page");
await page.goto(`${base}/connections`);
await page.getByRole("heading", { name: "Connect your stores" }).waitFor();
if (!(await page.getByRole("button", { name: /Connect Shopify/ }).isDisabled())) await fail("connect button should be disabled until filled in");

if (errors.length) await fail("page errors: " + errors.join(" | "));
await page.screenshot({ path: "e2e-result.png" });
console.log("PASS");
await browser.close();
