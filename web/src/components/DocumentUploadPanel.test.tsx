import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DocumentUploadPanel } from "./DocumentUploadPanel";
import type { IngestJob } from "../types";


function buildJob(overrides: Partial<IngestJob> = {}): IngestJob {
  return {
    job_id: "job-1",
    status: "running",
    progress: 45,
    message: "Processing upload.",
    knowledge_base: "math_docs",
    file_name: "algebra.pdf",
    parser_backend: "mineru",
    parse_method: "auto",
    requested_page: null,
    requested_start_page: 2,
    requested_end_page: 4,
    requested_page_count: 3,
    actual_processed_start_page: null,
    actual_processed_end_page: null,
    actual_processed_page_count: null,
    created_at: "2026-03-28T10:00:00+00:00",
    updated_at: "2026-03-28T10:02:00+00:00",
    started_at: "2026-03-28T10:00:30+00:00",
    completed_at: null,
    duration_ms: 1200,
    result: null,
    error: null,
    retry_of: null,
    cancel_requested: false,
    can_retry: false,
    can_cancel: true,
    ...overrides,
  };
}


describe("DocumentUploadPanel", () => {
  test("renders job history with parser and page details", () => {
    const currentJob = buildJob({ actual_processed_page_count: 2, actual_processed_start_page: 2, actual_processed_end_page: 3 });
    const historyJob = buildJob({ job_id: "job-2", file_name: "geometry.pdf", status: "completed", can_retry: true, can_cancel: false, actual_processed_page_count: 1, actual_processed_start_page: 1, actual_processed_end_page: 1 });

    render(
      <DocumentUploadPanel
        currentUploadJob={currentJob}
        isUploading={false}
        onCancelUpload={async () => {}}
        onRetryUpload={async () => {}}
        onUpload={async () => {}}
        recentUploadJobs={[currentJob, historyJob]}
        selectedKnowledgeBase="math_docs"
      />,
    );

    expect(screen.getByText("Recent Ingest Jobs")).toBeInTheDocument();
    expect(screen.getAllByText(/mineru\/auto/i)).toHaveLength(2);
    expect(screen.getAllByText(/processed 2 pages \(2-3\)/i)).toHaveLength(2);
    expect(screen.getByText(/processed 1 page \(1-1\)/i)).toBeInTheDocument();
    expect(screen.getByText("geometry.pdf")).toBeInTheDocument();
  });

  test("invokes cancel callback from current job controls", async () => {
    const user = userEvent.setup();
    const onCancelUpload = vi.fn().mockResolvedValue(undefined);

    render(
      <DocumentUploadPanel
        currentUploadJob={buildJob()}
        isUploading={false}
        onCancelUpload={onCancelUpload}
        onRetryUpload={async () => {}}
        onUpload={async () => {}}
        recentUploadJobs={[buildJob()]}
        selectedKnowledgeBase="math_docs"
      />,
    );

    await user.click(screen.getByRole("button", { name: "Cancel Job" }));

    await waitFor(() => expect(onCancelUpload).toHaveBeenCalledWith("job-1"));
    expect(screen.getByText("Cancellation request sent.")).toBeInTheDocument();
  });

  test("invokes retry callback from current job controls", async () => {
    const user = userEvent.setup();
    const onRetryUpload = vi.fn().mockResolvedValue(undefined);

    render(
      <DocumentUploadPanel
        currentUploadJob={buildJob({ status: "failed", can_retry: true, can_cancel: false })}
        isUploading={false}
        onCancelUpload={async () => {}}
        onRetryUpload={onRetryUpload}
        onUpload={async () => {}}
        recentUploadJobs={[buildJob({ status: "failed", can_retry: true, can_cancel: false })]}
        selectedKnowledgeBase="math_docs"
      />,
    );

    await user.click(screen.getByRole("button", { name: "Retry Job" }));

    await waitFor(() => expect(onRetryUpload).toHaveBeenCalledWith("job-1"));
    expect(screen.getByText("Retry started and completed successfully.")).toBeInTheDocument();
  });
});