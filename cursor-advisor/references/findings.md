# Findings and job state

`result` returns a wrapper with `status`, `job_id`, `cursor_session_id`, `model_id`, `actual_model`, `kind`, `read_only`, `source_changed_during_run`, `request_id` and the following `findings` object:

```json
{
  "kind": "review",
  "summary": "A concise evidence-based conclusion.",
  "findings": [
    {
      "severity": "high",
      "title": "A concrete defect or design risk",
      "file": "src/module.py",
      "line": 12,
      "evidence": "The trigger, observed behavior or source evidence.",
      "recommendation": "A suggested change for Codex to verify."
    }
  ],
  "questions": [],
  "limitations": [],
  "next_steps": []
}
```

`kind` is `review`, `debug`, or `architecture`; severity is `high`, `medium`, `low`, or `info`. Location may be null for cross-cutting findings. Empty findings are valid. Missing evidence or unavailable runtime verification belongs in limitations; architectural alternatives can be described in recommendations and next steps.

Each job stores `session.json`, a generated tool-restricted workspace and `runs/<request-uuid>/` containing prompt, invocation, stdout events, stderr and validated findings. Session IDs are Cursor IDs, not Codex thread IDs. A follow-up refreshes context but preserves the Cursor ID; old runs remain available. Different tasks use different job IDs.

States: `queued`, `running`, `completed`, `stale_context`, `failed`. Background `status` reports saved state rather than proving the process is healthy; inspect host/process and logs when a state stops progressing. `result` only returns validated findings for a completed/stale run, otherwise returns the current state/error. Do not describe an incomplete call as a successful review.
