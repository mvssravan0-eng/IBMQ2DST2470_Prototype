"""
run_all.py
----------
Runs the entire project end-to-end in order:
  1. data_loading   -- sanity check + dataset summary
  2. preprocessing  -- sanity check
  3. train_classification -- Part 1 (supervised)
  4. train_anomaly        -- Part 2 (unsupervised / zero-day)
  5. hybrid_pipeline       -- Part 3 (combined system)

All plots land in outputs/plots/, all tables in outputs/tables/.
Run with:  python3 src/run_all.py
"""

import time


def section(title):
    print("\n" + "#" * 78)
    print(f"# {title}")
    print("#" * 78 + "\n")


def main():
    t0 = time.time()

    section("STEP 1/5: Loading & inspecting NSL-KDD dataset")
    import data_loading
    train_df, test_df = data_loading.load_nslkdd("../data")
    data_loading.summarize(train_df, test_df)

    section("STEP 2/5: PART 1 -- Supervised classification (known attacks)")
    import train_classification
    train_classification.main()

    section("STEP 3/5: PART 2 -- Unsupervised anomaly detection (zero-day)")
    import train_anomaly
    train_anomaly.main()

    section("STEP 4/5: PART 3 -- Hybrid combined pipeline")
    import hybrid_pipeline
    hybrid_pipeline.main()

    section("STEP 5/5: Explainability -- SHAP analysis on the classifier")
    import shap_analysis
    shap_analysis.main()

    elapsed = time.time() - t0
    section(f"DONE in {elapsed:.1f}s -- see outputs/plots/ and outputs/tables/")


if __name__ == "__main__":
    main()
