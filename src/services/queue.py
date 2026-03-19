"""
Priority Request Queue

Redis-backed priority queue using sorted sets.
Score = (priority × 1e12) + timestamp for priority-then-FIFO ordering.

Includes a background worker that dequeues and dispatches to inference.
"""

# TODO: Phase 3 - RequestQueue class (enqueue, dequeue)
# TODO: Phase 3 - QueueWorker background task
# TODO: Phase 3 - Bounded capacity with 503 backpressure
