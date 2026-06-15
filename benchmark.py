"""
Kakashi v0.2.2 Benchmark — vs stdlib, loguru, structlog

Measures:
  1. Single-thread throughput (logs/sec)
  2. 16-thread concurrency scaling factor
  3. Kakashi async throughput (logs/sec)
"""

import io
import logging
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(__file__))

from kakashi import get_logger, get_async_logger, shutdown_async_logging

# Suppress all output to /dev/null for fair comparison
DEVNULL = open(os.devnull, "w")
_real_stderr = sys.stderr

TOTAL_LOGS = 100_000
CONCURRENT_LOGS = 80_000
NUM_THREADS = 16
MESSAGES_PER_THREAD = CONCURRENT_LOGS // NUM_THREADS
ASYNC_TOTAL = 100_000


# ── Helpers ──────────────────────────────────────────────────────────

def make_stdlib_logger():
    logger = logging.getLogger("bench.stdlib")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(DEVNULL)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def make_loguru_logger():
    from loguru import logger as _loguru_logger
    _loguru_logger.remove()
    _loguru_logger.add(DEVNULL, level="INFO")
    return _loguru_logger


def make_structlog_logger():
    import structlog
    structlog.configure(
        processors=[structlog.processors.JSONRenderer()],
        wrapper_class=structlog.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=DEVNULL),
    )
    return structlog.get_logger("bench.structlog")


def bench_throughput(name, log_fn, n=TOTAL_LOGS, redirect_stderr=False):
    if redirect_stderr:
        sys.stderr = DEVNULL
    t0 = time.perf_counter()
    for i in range(n):
        log_fn(i)
    elapsed = time.perf_counter() - t0
    if redirect_stderr:
        sys.stderr = _real_stderr
    lps = n / elapsed
    return {"name": name, "logs_per_sec": lps, "elapsed": elapsed, "total": n}


def bench_concurrency(name, log_fn, n_per_thread=MESSAGES_PER_THREAD, threads=NUM_THREADS, redirect_stderr=False):
    def worker():
        for i in range(n_per_thread):
            log_fn(i)

    total = n_per_thread * threads
    if redirect_stderr:
        sys.stderr = DEVNULL
    t0 = time.perf_counter()
    workers = [threading.Thread(target=worker) for _ in range(threads)]
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    elapsed = time.perf_counter() - t0
    if redirect_stderr:
        sys.stderr = _real_stderr
    lps = total / elapsed
    return {"name": name, "logs_per_sec": lps, "elapsed": elapsed, "total": total, "threads": threads}


def bench_async_throughput(n=ASYNC_TOTAL):
    logger = get_async_logger("bench.async")
    t0 = time.perf_counter()
    for i in range(n):
        logger.info(f"Async benchmark message {i}")
    logger.flush()
    elapsed = time.perf_counter() - t0
    lps = n / elapsed
    shutdown_async_logging()
    return {"name": "Kakashi Async", "logs_per_sec": lps, "elapsed": elapsed, "total": n}


# ── Run ──────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  KAKASHI v0.2.2 — Performance Benchmark")
    print("=" * 70)

    # System info
    import platform
    print(f"\n  Python: {sys.version.split()[0]}")
    print(f"  Platform: {platform.platform()}")
    print(f"  CPU cores: {os.cpu_count()}")
    print(f"  Total logs per test: {TOTAL_LOGS:,}")
    print(f"  Concurrent threads: {NUM_THREADS}")

    # ── Setup loggers ────────────────────────────────────────────────
    kakashi_sync = get_logger("bench.kakashi")
    stdlib = make_stdlib_logger()
    loguru_l = make_loguru_logger()
    structlog_l = make_structlog_logger()

    # ── 1. Single-thread throughput ──────────────────────────────────
    print("\n" + "─" * 70)
    print("  TEST 1: Single-Thread Throughput")
    print("─" * 70)

    results = []
    results.append(bench_throughput("Kakashi", lambda i: kakashi_sync.info(f"Benchmark message {i}"), redirect_stderr=True))
    results.append(bench_throughput("Standard Library", lambda i: stdlib.info(f"Benchmark message {i}")))
    results.append(bench_throughput("Loguru", lambda i: loguru_l.info(f"Benchmark message {i}")))
    results.append(bench_throughput("Structlog", lambda i: structlog_l.info(message="Benchmark message", seq=i)))

    results.sort(key=lambda r: r["logs_per_sec"], reverse=True)
    best = results[0]["logs_per_sec"]
    print(f"\n  {'Library':<20} {'logs/sec':>12}  {'vs Kakashi':>10}")
    print(f"  {'─'*20} {'─'*12}  {'─'*10}")
    for r in results:
        ratio = r["logs_per_sec"] / best * 100
        marker = " ★" if r["name"] == "Kakashi" else ""
        print(f"  {r['name']:<20} {r['logs_per_sec']:>12,.0f}  {ratio:>9.1f}%{marker}")

    # ── 2. Concurrency scaling ───────────────────────────────────────
    print("\n" + "─" * 70)
    print(f"  TEST 2: Concurrency Scaling ({NUM_THREADS} threads, {CONCURRENT_LOGS:,} total logs)")
    print("─" * 70)

    conc = []
    conc.append(bench_concurrency("Kakashi", lambda i: kakashi_sync.info(f"Concurrent message {i}"), redirect_stderr=True))
    conc.append(bench_concurrency("Standard Library", lambda i: stdlib.info(f"Concurrent message {i}")))
    conc.append(bench_concurrency("Loguru", lambda i: loguru_l.info(f"Concurrent message {i}")))
    conc.append(bench_concurrency("Structlog", lambda i: structlog_l.info(message="Concurrent message", seq=i)))

    # Compute scaling factor: concurrent_lps / single_lps
    single_map = {r["name"]: r["logs_per_sec"] for r in results}
    conc.sort(key=lambda r: r["logs_per_sec"], reverse=True)
    best_conc = conc[0]["logs_per_sec"]

    print(f"\n  {'Library':<20} {'logs/sec':>12}  {'Scaling':>8}  {'vs Kakashi':>10}")
    print(f"  {'─'*20} {'─'*12}  {'─'*8}  {'─'*10}")
    for r in conc:
        single = single_map.get(r["name"], r["logs_per_sec"])
        scaling = r["logs_per_sec"] / single if single else 0
        ratio = r["logs_per_sec"] / best_conc * 100
        marker = " ★" if r["name"] == "Kakashi" else ""
        print(f"  {r['name']:<20} {r['logs_per_sec']:>12,.0f}  {scaling:>7.2f}x  {ratio:>9.1f}%{marker}")

    # ── 3. Async throughput (Kakashi only) ───────────────────────────
    print("\n" + "─" * 70)
    print("  TEST 3: Kakashi Async Throughput")
    print("─" * 70)

    async_result = bench_async_throughput()
    print(f"\n  {'Library':<20} {'logs/sec':>12}")
    print(f"  {'─'*20} {'─'*12}")
    print(f"  {async_result['name']:<20} {async_result['logs_per_sec']:>12,.0f} ★")

    # ── Summary table ────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)

    single_map = {r["name"]: r["logs_per_sec"] for r in results}
    conc_map = {r["name"]: r for r in conc}

    print(f"\n  {'Library':<20} {'Throughput':>12} {'Concurrency':>14} {'Scaling':>8}")
    print(f"  {'─'*20} {'─'*12} {'─'*14} {'─'*8}")

    for name in ["Kakashi", "Standard Library", "Loguru", "Structlog"]:
        t = single_map.get(name, 0)
        c = conc_map.get(name, {})
        cl = c.get("logs_per_sec", 0)
        scaling = cl / t if t else 0
        async_note = f"{async_result['logs_per_sec']:>12,.0f}" if name == "Kakashi" else "N/A"
        print(f"  {name:<20} {t:>12,.0f} {cl:>12,.0f}  {scaling:>7.2f}x")

    print(f"\n  Kakashi Async: {async_result['logs_per_sec']:,.0f} logs/sec")
    print("=" * 70)

    # Save results to JSON
    import json
    out = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "kakashi_version": "0.2.2",
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "single_thread_throughput": {r["name"]: round(r["logs_per_sec"]) for r in results},
        "concurrency_scaling": {
            r["name"]: {
                "logs_per_sec": round(r["logs_per_sec"]),
                "scaling_factor": round(r["logs_per_sec"] / single_map.get(r["name"], 1), 2),
            }
            for r in conc
        },
        "async_throughput": round(async_result["logs_per_sec"]),
    }
    with open("kakashi_benchmark_results.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n  Results saved to kakashi_benchmark_results.json")


if __name__ == "__main__":
    main()
