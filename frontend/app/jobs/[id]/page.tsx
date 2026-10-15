"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Plus } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Progress } from "@/components/progress";
import { Results } from "@/components/results";
import { Card } from "@/components/ui";
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

  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-4 pb-safe pt-6 sm:px-6">
      <div className="mb-4 flex items-center justify-between">
        <Link href="/" className="inline-flex min-h-11 items-center gap-1.5 text-sm text-muted hover:text-foreground"><ArrowLeft className="size-4" />Home</Link>
        <Link href="/create" className="inline-flex min-h-11 items-center gap-1.5 text-sm text-accent"><Plus className="size-4" />New kit</Link>
      </div>
      {error && <Card><p role="alert" className="text-danger">{(error as ApiError).message}</p></Card>}
      {!job && !error && <p className="text-muted">Loading…</p>}
      {job && (
        <>
          <h1 className="mb-5 text-2xl font-semibold tracking-tight">{job.product.name}</h1>
          {job.status === "completed" && job.copy_output ? (
            <Results job={job} />
          ) : (
            <Card><Progress job={job} onRetry={() => retry.mutate()} retrying={retry.isPending} /></Card>
          )}
        </>
      )}
    </main>
  );
}
