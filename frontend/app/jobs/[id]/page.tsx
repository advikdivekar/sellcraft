"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
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

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 space-y-6 px-4 pb-safe pt-6 sm:px-6">
      {error && <Card><p role="alert" className="font-medium text-danger">{(error as ApiError).message}</p><Link href="/create" className="mt-2 inline-block text-sm font-medium text-accent-text underline">Start a new kit</Link></Card>}
      {!job && !error && <div className="space-y-4"><Skeleton className="h-9 w-64" /><Skeleton className="h-12 w-full" /><Skeleton className="h-96 w-full" /></div>}
      {job && (
        <>
          {working && (
            <Card className="anim-in mx-auto w-full max-w-2xl space-y-1">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div><h1 className="text-xl font-semibold tracking-tight">{job.status === "failed" ? "Something went wrong" : "Building your kit"}</h1>
                  <p className="text-sm text-muted">{job.product.name}. {job.status === "failed" ? "" : "You can leave this page; it keeps running."}</p></div>
              </div>
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
