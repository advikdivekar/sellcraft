/** Downscale + re-encode a phone photo to JPEG before upload (keeps uploads small, converts HEIC on Safari). */
export async function prepareImage(file: File, maxSide = 2048): Promise<Blob> {
  const okTypes = ["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif", ""];
  if (!okTypes.includes(file.type)) throw new Error("Use a JPEG, PNG or WebP photo.");
  let bitmap: ImageBitmap;
  try {
    bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
  } catch {
    throw new Error("This browser can't read that image. Try a JPEG, PNG or WebP photo.");
  }
  const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height));
  const w = Math.round(bitmap.width * scale), h = Math.round(bitmap.height * scale);
  const canvas = document.createElement("canvas");
  canvas.width = w; canvas.height = h;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Couldn't process the image.");
  if (file.type !== "image/png") { ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, w, h); }
  ctx.drawImage(bitmap, 0, 0, w, h);
  bitmap.close();
  const png = file.type === "image/png";
  const blob = await new Promise<Blob | null>((r) => canvas.toBlob(r, png ? "image/png" : "image/jpeg", 0.9));
  if (!blob) throw new Error("Couldn't process the image.");
  return blob;
}

export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(ta);
    return ok;
  }
}
