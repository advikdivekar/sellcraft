"use client";
import { Camera, ImagePlus, RefreshCw, Trash2 } from "lucide-react";
import { useRef, useState } from "react";
import { api } from "@/lib/api";
import { prepareImage } from "@/lib/image";
import { Button } from "./ui";

export interface UploadedImage { assetId: string; previewUrl: string }

export function ImageDropzone({ value, onChange }: { value: UploadedImage | null; onChange: (v: UploadedImage | null) => void }) {
  const gallery = useRef<HTMLInputElement>(null);
  const camera = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handle(file: File | undefined) {
    if (!file) return;
    setError(null);
    setBusy(true);
    try {
      const blob = await prepareImage(file);
      const res = await api.upload(blob, file.name);
      if (value) URL.revokeObjectURL(value.previewUrl);
      onChange({ assetId: res.asset_id, previewUrl: URL.createObjectURL(blob) });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed.");
    } finally {
      setBusy(false);
      if (gallery.current) gallery.current.value = "";
      if (camera.current) camera.current.value = "";
    }
  }

  const accept = "image/jpeg,image/png,image/webp,image/heic,image/heif";
  return (
    <div>
      <input ref={gallery} type="file" accept={accept} className="sr-only" aria-label="Choose product photo" onChange={(e) => handle(e.target.files?.[0])} />
      <input ref={camera} type="file" accept="image/*" capture="environment" className="sr-only" aria-label="Take product photo" onChange={(e) => handle(e.target.files?.[0])} />
      {value ? (
        <div className="space-y-3">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={value.previewUrl} alt="Your product photo" className="max-h-80 w-full rounded-xl border border-border bg-background object-contain" />
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" size="sm" busy={busy} onClick={() => gallery.current?.click()}><RefreshCw className="size-4" />Replace</Button>
            <Button variant="ghost" size="sm" onClick={() => { URL.revokeObjectURL(value.previewUrl); onChange(null); }}><Trash2 className="size-4" />Remove</Button>
          </div>
        </div>
      ) : (
        <div className="rounded-xl border-2 border-dashed border-border bg-background p-6 text-center">
          <ImagePlus className="mx-auto mb-2 size-8 text-muted" aria-hidden />
          <p className="mb-4 text-sm text-muted">JPEG, PNG or WebP. A clear photo on a plain background works best.</p>
          <div className="flex flex-col gap-2 sm:flex-row sm:justify-center">
            <Button busy={busy} onClick={() => camera.current?.click()}><Camera className="size-5" />Take photo</Button>
            <Button variant="secondary" busy={busy} onClick={() => gallery.current?.click()}><ImagePlus className="size-5" />Choose from library</Button>
          </div>
        </div>
      )}
      {error && <p role="alert" className="mt-2 text-sm text-danger">{error}</p>}
    </div>
  );
}
