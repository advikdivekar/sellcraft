import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Mochi",
    short_name: "Mochi",
    description: "Your product. Your story. Ready to sell.",
    start_url: "/create",
    display: "standalone",
    orientation: "portrait",
    background_color: "#00282C",
    theme_color: "#00282C",
    icons: [
      { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png" },
      { src: "/icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}
