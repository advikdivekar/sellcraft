"use client";
import { Camera, ImagePlus, Loader2, Sparkles, Star, X } from "lucide-react";
import { useRef, useState } from "react";
import { api } from "@/lib/api";
import { prepareImage } from "@/lib/image";
import { Button } from "./ui";

export interface UploadedImage { assetId: string; previewUrl: string }
export const MAX_PHOTOS = 5;

type Update = (fn: (cur: UploadedImage[]) => UploadedImage[]) => void;

export function ImageDropzone({ value, update, onAdded }: {
  value: UploadedImage[]; update: Update; onAdded: () => void;
}) {
  const gallery = useRef<HTMLInputElement>(null);
  const camera = useRef<HTMLInputElement>(null);
  const [pending, setPending] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const room = MAX_PHOTOS - value.length - pending;

  async function sample() {
    try {
      const blob = await (await fetch("/sample-product.png")).blob();
      await handle([new File([blob], "sample-candle.png", { type: "image/png" })]);
    } catch { setError("Couldn't load the sample photo."); }
  }
  async function handle(files: FileList | File[] | null) {
    if (!files || files.length === 0) return;
    setError(null);
    const picked = Array.from(files).slice(0, Math.max(0, room));
    if (files.length > picked.length) setError(`You can add up to ${MAX_PHOTOS} photos. Extra ones were skipped.`);
    setPending((n) => n + picked.length);
    const done: UploadedImage[] = [];
    await Promise.all(picked.map(async (file) => {
      try {
        const blob = await prepareImage(file);
        const res = await api.upload(blob, file.name);
        done.push({ assetId: res.asset_id, previewUrl: URL.createObjectURL(blob) });
      } catch (e) {
        setError(e instanceof Error ? e.message : "Upload failed.");
      } finally {
        setPending((n) => n - 1);
      }
    }));
    if (done.length) { update((cur) => [...cur, ...done].slice(0, MAX_PHOTOS)); onAdded(); }
    if (gallery.current) gallery.current.value = "";
    if (camera.current) camera.current.value = "";
  }

  const remove = (i: number) => update((cur) => { URL.revokeObjectURL(cur[i].previewUrl); return cur.filter((_, j) => j !== i); });
  const makeMain = (i: number) => update((cur) => [cur[i], ...cur.filter((_, j) => j !== i)]);
  const accept = "image/jpeg,image/png,image/webp,image/heic,image/heif";

  return (
    <div className="space-y-3">
      <input ref={gallery} type="file" multiple accept={accept} className="sr-only" aria-label="Choose product photos" onChange={(e) => handle(e.target.files)} />
      <input ref={camera} type="file" accept="image/*" capture="environment" className="sr-only" aria-label="Take product photo" onChange={(e) => handle(e.target.files)} />

      {(value.length > 0 || pending > 0) && (
        <ul className="grid grid-cols-3 gap-2" aria-label="Your photos">
          {value.map((img, i) => (
            <li key={img.assetId} className="relative aspect-square overflow-hidden rounded-xl bg-surface-2 ring-1 ring-border">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={img.previewUrl} alt={`Product photo ${i + 1}`} className="size-full object-cover" />
              {i === 0 && <span className="absolute left-1.5 top-1.5 rounded-full bg-accent px-2 py-0.5 text-[11px] font-semibold text-accent-fg">Main</span>}
              <button type="button" aria-label={`Remove photo ${i + 1}`} onClick={() => remove(i)}
                className="absolute right-1 top-1 grid size-9 place-items-center rounded-full bg-black/60 text-white"><X className="size-4" /></button>
              {i > 0 && (
                <button type="button" aria-label={`Make photo ${i + 1} the main photo`} onClick={() => makeMain(i)}
                  className="absolute bottom-1 left-1 inline-flex h-9 items-center gap-1 rounded-full bg-black/60 px-2.5 text-xs text-white"><Star className="size-3.5" />Main</button>
              )}
            </li>
          ))}
          {Array.from({ length: pending }).map((_, i) => (
            <li key={`p${i}`} className="grid aspect-square place-items-center rounded-xl border border-dashed border-border bg-background" role="status" aria-label="Uploading">
              <Loader2 className="size-5 animate-spin text-muted" />
            </li>
          ))}
        </ul>
      )}

      {room > 0 && (
        <div className={value.length === 0 && pending === 0 ? "rounded-xl border border-dashed border-border-strong bg-surface-2 px-5 py-9 text-center" : ""}>
          {value.length === 0 && pending === 0 && (
            <>
              <span className="mx-auto mb-3 grid size-12 place-items-center rounded-full bg-surface shadow-card ring-1 ring-border"><ImagePlus className="size-5 text-muted" aria-hidden /></span>
              <p className="mb-4 text-sm text-muted">Add up to {MAX_PHOTOS} photos: different angles help. A clear photo on a plain background works best.</p>
            </>
          )}
          <div className="flex flex-col gap-2 sm:flex-row sm:justify-center">
            <Button onClick={() => camera.current?.click()} size="lg"><Camera className="size-5" />Take photo</Button>
            <Button variant="secondary" size="lg" onClick={() => gallery.current?.click()}><ImagePlus className="size-5" />{value.length ? "Add more" : "Choose from library"}</Button>
          </div>
          {value.length === 0 && pending === 0 && (
            <button type="button" onClick={sample} className="mt-3 inline-flex min-h-11 items-center gap-1.5 rounded-full px-3 text-sm font-medium text-accent-text transition hover:bg-accent-soft">
              <Sparkles className="size-4" aria-hidden />No photo handy? Try a sample product
            </button>
          )}
        </div>
      )}
      <p className="text-xs text-muted">{value.length}/{MAX_PHOTOS} photos. The <strong>Main</strong> photo opens and closes your video.</p>
      {error && <p role="alert" className="text-sm text-danger">{error}</p>}
    </div>
  );
}
