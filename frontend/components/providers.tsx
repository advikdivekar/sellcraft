"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { AccessGate } from "./access-gate";
import { AppShell } from "./app-shell";
import { FeedbackProvider } from "./feedback";

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(
    () => new QueryClient({ defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } } }),
  );
  return <QueryClientProvider client={client}><AccessGate><FeedbackProvider><AppShell>{children}</AppShell></FeedbackProvider></AccessGate></QueryClientProvider>;
}
