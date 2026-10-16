"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { BuildingHero } from "@/components/building";
import { useFeedback } from "@/components/feedback";
import { Progress } from "@/components/progress";
import { Results } from "@/components/results";
import { Card, Skeleton } from "@/components/ui";
import { ApiError, api } from "@/lib/api";

export default function JobPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const { data: job, error } = useQuery({
    queryKey: ["job", id],
    queryFn: () => api.getJob(id),
    refetchInterval: (q) => (["completed", "failed"].includes(q.state.data?.status ?? "") ? false : 1500),
  });
  const retry = useMutation({ mutationFn: () => api.retry(id), onSuccess: (j) => qc.setQueryData(["job", id], j) });
  const working = job && job.status !== "completed";
  const { toast } = useFeedback();
  const [startedAt] = useState(() => Date.now());
  const wasWorking = useRef(false);
  const status = job?.status;
  useEffect(() => {
    if (!status) return;
    if (status !== "completed" && status !== "failed") { wasWorking.current = true; return; }
    if (status === "completed" && wasWorking.current) {  // finished while the seller was watching: a small moment of delight
      wasWorking.current = false;
      toast(`Your kit is ready · built in ${Math.max(1, Math.round((Date.now() - startedAt) / 1000))} s`);
      try { navigator.vibrate?.(25); } catch { /* not supported */ }
    }
  }, [status, startedAt, toast]);

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 space-y-6 px-4 pb-safe pt-6 sm:px-6">
      {error && <Card><p role="alert" className="font-medium text-danger">{(error as ApiError).message}</p><Link href="/create" className="mt-2 inline-block text-sm font-medium text-accent-text underline">Start a new kit</Link></Card>}
      {!job && !error && <div className="space-y-4"><Skeleton className="h-9 w-64" /><Skeleton className="h-12 w-full" /><Skeleton className="h-96 w-full" /></div>}
      {job && (
        <>
          {working && (
            <Card className="anim-in mx-auto w-full max-w-2xl space-y-1">
              {job.status === "failed"
                ? <div className="mb-3"><h1 className="text-xl font-semibold tracking-tight">Something went wrong</h1><p className="text-sm text-muted">{job.product.name}</p></div>
                : <div className="mb-4"><BuildingHero job={job} startedAt={startedAt} /><p className="mt-3 text-xs text-muted">{job.product.name}. You can leave this page; it keeps running.</p></div>}
              <Progress job={job} onRetry={() => retry.mutate()} retrying={retry.isPending} />
            </Card>
          )}
          {job.copy_output && <Results job={job} />}
          {job.status === "completed" && (
            <div className="flex justify-center pt-2"><Link href="/create" className="inline-flex min-h-12 items-center gap-2 rounded-xl border border-border-strong bg-surface px-5 font-medium shadow-card transition hover:bg-surface-2"><Plus className="size-4" />Create another kit</Link></div>
          )}
        </>
      )}
    </main>
  );
}
