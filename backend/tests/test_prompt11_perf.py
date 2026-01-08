from backend.coverage_perf import chunk_global_combined, global_combined_scenarios


def test_chunking_and_metrics():
    chunks, m = chunk_global_combined(chunk_size=250)
    assert m.total > 0
    assert m.chunks >= 1
    assert m.max_chunk <= 250
    # Recompute scenarios and verify counts match
    all_sc = global_combined_scenarios()
    assert sum(len(c) for c in chunks) == len(all_sc)


def test_max_total_guard():
    chunks, m = chunk_global_combined(chunk_size=9999)
    # Now enforce max_total below actual to trigger error
    try:
        chunk_global_combined(chunk_size=9999, max_total=m.total - 1)
    except RuntimeError:
        pass
    else:
        assert False, "Expected RuntimeError for exceeding max_total"
