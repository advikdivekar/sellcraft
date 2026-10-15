export interface ShareFile { url: string; name: string; type: string }

/** Open the phone's share sheet with real files (video, slides). Falls back to opening the first file. */
export async function shareFiles(files: ShareFile[], opts: { text?: string; title?: string } = {}): Promise<"shared" | "fallback" | "cancelled"> {
  try {
    const blobs = await Promise.all(files.map(async (f) => new File([await (await fetch(f.url)).blob()], f.name, { type: f.type })));
    if (navigator.canShare?.({ files: blobs })) {
      await navigator.share({ files: blobs, text: opts.text, title: opts.title });
      return "shared";
    }
  } catch (e) {
    if ((e as Error).name === "AbortError") return "cancelled";
  }
  if (files[0]) window.open(files[0].url, "_blank");
  return "fallback";
}

export function downloadText(name: string, text: string, type = "text/plain") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = Object.assign(document.createElement("a"), { href: url, download: name });
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "product";
