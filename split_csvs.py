import os
import pandas as pd

SOURCE_DIR = os.path.join(os.path.dirname(__file__), "data", "TEOS IRS Data", "actual")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data", "TEOS IRS Data")
MAX_SIZE_MB = 50
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024

os.makedirs(OUTPUT_DIR, exist_ok=True)

csv_files = [f for f in os.listdir(SOURCE_DIR) if f.endswith(".csv")]

for csv_file in sorted(csv_files):
    base_name = os.path.splitext(csv_file)[0]  # e.g. "eo1"
    source_path = os.path.join(SOURCE_DIR, csv_file)
    file_size = os.path.getsize(source_path)

    if file_size <= MAX_SIZE_BYTES:
        print(f"{csv_file} is under 50 MB ({file_size / 1024 / 1024:.1f} MB), skipping split.")
        continue

    print(f"Splitting {csv_file} ({file_size / 1024 / 1024:.1f} MB)...")

    df = pd.read_csv(source_path, low_memory=False)
    total_rows = len(df)

    # Estimate rows per chunk based on file size ratio
    rows_per_chunk = max(1, int(total_rows * MAX_SIZE_BYTES / file_size))

    chunk_num = 1
    start = 0
    while start < total_rows:
        chunk = df.iloc[start:start + rows_per_chunk]
        out_path = os.path.join(OUTPUT_DIR, f"{base_name}_{chunk_num}.csv")

        chunk.to_csv(out_path, index=False)

        actual_size = os.path.getsize(out_path)
        print(f"  -> {base_name}_{chunk_num}.csv ({actual_size / 1024 / 1024:.1f} MB, {len(chunk)} rows)")

        start += rows_per_chunk
        chunk_num += 1

print("Done.")
