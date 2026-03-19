# Concept: Request Queuing

## What Is It?

A request queue sits between the API gateway and the model server. It absorbs
bursts of traffic, enforces priority ordering, and provides backpressure when
the system is overloaded.

## Why Does It Exist?

Your GPU can only process so many requests at once. Without a queue:
- Burst traffic gets immediately rejected
- No way to prioritize paying users over free users
- No backpressure signal ("the system is full")
- No fairness guarantee

## Real-World Analogy

Think of a hospital emergency room:
- Patients (requests) arrive unpredictably
- Triage nurse (API gateway) assigns priority: critical, urgent, standard
- Waiting room (queue) holds patients until a doctor (GPU) is free
- Critical patients are seen first, regardless of arrival time
- If the waiting room is full, ambulances are diverted (503 Service Unavailable)

## How It Works

### Priority Levels

```
Priority 0 (admin):  ████░░░░░░  Processed FIRST
Priority 1 (pro):    ██████░░░░  Processed SECOND
Priority 2 (free):   ████████░░  Processed LAST

Within each priority: First-Come, First-Served (FIFO)
```

### Redis Sorted Set Implementation

Redis sorted sets (ZSET) are perfect for priority queues:

```
Key: "request_queue"
Score: (priority × 1,000,000,000,000) + unix_timestamp_ms

Example entries:
  score: 0_001710769260000  → admin request at time T      (served 1st)
  score: 1_001710769255000  → pro request at time T-5s      (served 2nd)
  score: 1_001710769260000  → pro request at time T          (served 3rd)
  score: 2_001710769250000  → free request at time T-10s     (served 4th)
```

The genius: `ZPOPMIN` always gives you the lowest score = highest priority + earliest arrival.

### Backpressure

```
Queue capacity: 100 requests

Queue depth: 95/100
  → Accept request, warn in logs

Queue depth: 100/100
  → Reject with 503 Service Unavailable
  → This IS the backpressure signal

Queue depth drops to 80/100
  → Accept requests again
```

### Queue Worker

An asyncio background task constantly dequeues and dispatches:

```python
# Simplified concept
while running:
    request = await queue.pop_highest_priority()
    if request:
        async with semaphore:  # limit concurrent GPU requests
            await inference_service.process(request)
    else:
        await asyncio.sleep(0.01)  # don't spin-wait
```

The semaphore controls how many requests hit vLLM simultaneously (matching
the GPU's capacity for concurrent inference).

## What Frontier Labs Do Differently

| Yours | Frontier Lab |
|-------|-------------|
| Redis sorted set | Kafka / custom distributed queue |
| 100 request capacity | Millions in queue |
| Single consumer | Thousands of consumers across GPU clusters |
| Simple priority FIFO | Fair scheduling, SLO-based routing, request coalescing |
| asyncio Semaphore | Kubernetes-managed pod autoscaling |

## Files You'll Build

| File | Purpose |
|------|---------|
| `src/services/queue.py` | Priority queue + worker dispatcher |
| `src/models/enums.py` | Priority level enum |
| `tests/unit/test_queue.py` | Priority ordering, capacity limits |
