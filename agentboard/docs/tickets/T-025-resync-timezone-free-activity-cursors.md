---
name: "T-025 — Resync timezone-free activity cursors"
description: "Reconnects the activity stream when a cursor timestamp lacks a timezone."
kind: "ticket"
tags: ["feature:progress-tracking", "concern:reliability"]
---

# T-025 — Resync timezone-free activity cursors

Role: BE
Type: BUG
Status: Done
Verification: Fixed
Assignment: Confirmed
Depends on: None
Estimate (days): 0.25
Estimate scope: Repair
Estimate basis: Targeted reconnect validation, local backend rebuild, and regression check.

## Outcome

A malformed reconnect cursor leads to a resync event and a usable activity stream.

## User Report

Discovered during the local release check. The running API returned HTTP 500 when an authenticated `GET /events` request sent a base64url `Last-Event-ID` containing a valid UUID and an ISO timestamp without a timezone.

## Investigation

The cursor parser accepted the timestamp as a timezone-free datetime. Comparing it with the UTC retention cutoff raised a type error before streaming began.

## Acceptance Criteria

- Treat timezone-free timestamps as malformed cursors and emit a resync event.
- Preserve resync behavior for an expired cursor with an explicit timezone.

## Context

- [T-011 — Stream committed project events](T-011-stream-committed-project-events.md)
- [T-020 — Verify persisted desktop journeys](T-020-verify-persisted-desktop-user-journeys.md)
- [Activity stream handler](../../backend/app/main.py)

## Completion Evidence

The same authenticated request returned HTTP 200 and `event: resync` after backend recreation. An explicitly expired UTC cursor also emitted resync. See the [review report](../review-report.md).
