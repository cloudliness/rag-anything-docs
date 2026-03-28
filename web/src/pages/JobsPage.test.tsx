import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { JobsPage } from "./JobsPage";
import type { IngestJob, KnowledgeBase } from "../types";


function buildJob(overrides: Partial<IngestJob> = {}): IngestJob {
  return {
    job_id: "job-1",
    status: "completed",
    progress: 100,
    message: "Completed.",
    knowledge_base: "math_docs",
    file_name: "algebra.pdf",
    parser_backend: "mineru",
    parse_method: "auto",
    requested_page: null,
    requested_start_page: 1,
    requested_end_page: 3,
    requested_page_count: 3,
    actual_processed_start_page: 1,
    actual_processed_end_page: 2,
    actual_processed_page_count: 2,
    created_at: "2026-03-28T10:00:00+00:00",
    updated_at: "2026-03-28T10:05:00+00:00",
    started_at: "2026-03-28T10:00:30+00:00",
    completed_at: "2026-03-28T10:05:00+00:00",
    duration_ms: 4500,
    result: null,
    error: null,
    retry_of: null,
    cancel_requested: false,
    can_retry: true,
    can_cancel: false,
    ...overrides,
  };
}


describe("JobsPage", () => {
  const knowledgeBases: KnowledgeBase[] = [
    { name: "math_docs", document_count: 1 },
    { name: "physics_docs", document_count: 1 },
  ];

  test("filters jobs by status and search term", async () => {
    const user = userEvent.setup();
    const jobs = [
      buildJob({ job_id: "job-1", file_name: "algebra.pdf", status: "completed" }),
      buildJob({ job_id: "job-2", file_name: "mechanics.pdf", knowledge_base: "physics_docs", status: "failed" }),
    ];

    render(
      <JobsPage
        isUploading={false}
        jobs={jobs}
        knowledgeBases={knowledgeBases}
        onCancelUpload={async () => {}}
        onRetryUpload={async () => {}}
      />,
    );

    await user.selectOptions(screen.getByLabelText("Filter by status"), "failed");
    await user.type(screen.getByLabelText("Search jobs"), "mech");

    expect(screen.getByRole("heading", { name: "mechanics.pdf" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "algebra.pdf" })).not.toBeInTheDocument();
  });

  test("sorts jobs by duration descending", async () => {
    const user = userEvent.setup();
    const jobs = [
      buildJob({ job_id: "job-1", file_name: "fast.pdf", duration_ms: 1000 }),
      buildJob({ job_id: "job-2", file_name: "slow.pdf", duration_ms: 5000 }),
    ];

    render(
      <JobsPage
        isUploading={false}
        jobs={jobs}
        knowledgeBases={knowledgeBases}
        onCancelUpload={async () => {}}
        onRetryUpload={async () => {}}
      />,
    );

    await user.selectOptions(screen.getByLabelText("Sort jobs"), "duration-desc");

    const headings = screen.getAllByRole("heading", { level: 3 }).map((heading) => heading.textContent);
    expect(headings[0]).toBe("slow.pdf");
    expect(headings[1]).toBe("fast.pdf");
  });
});