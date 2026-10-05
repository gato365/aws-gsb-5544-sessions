---
title: "Optional Reading: Extraction Strategies and Cost Detail"
---

**GSB 5544 · Optional. Not required for the first session.**

*These exercises and cost tables were part of the pre-class reading and were moved here to keep that reading manageable. They are worth your time once the required workflow feels comfortable. Everything on this page runs on your laptop, in Positron, in the same notebook you used for the reading: it needs the `human()` helper from section 2 and the `s3` client and `BUCKET` from section 4.*

::: {.callout-note title="This is not the required workflow"}
The cells here read from S3 straight into your laptop. That is useful for learning how S3 behaves, and it is fine for small objects. It is **not** the remote-computation workflow that the practice activity and the lab require, where a SageMaker machine does the reading and summarizing.
:::

---

## 1. Looking before you read

### Listing, not downloading

The first thing to do with any bucket is look at what is in it. `Delimiter="/"` asks S3 to group keys by their first path segment, which is how you see the "folders":

```python
# RUNS ON: laptop (Positron)
resp = s3.list_objects_v2(Bucket=BUCKET, Delimiter="/")
print([p["Prefix"] for p in resp.get("CommonPrefixes", [])])
print([o["Key"] for o in resp.get("Contents", [])][:6])
```

**What this code does.**

- `s3.list_objects_v2(Bucket=BUCKET, Delimiter="/")` sends one request that asks, "what is at the top level of this bucket?" The answer comes back as a Python dictionary. No file contents are transferred, only names and metadata.
- `resp["CommonPrefixes"]` holds the "folders": every distinct beginning of a key up to the first `/`.
- `resp["Contents"]` holds the objects that sit at the top level with no `/` in their key.
- `.get("CommonPrefixes", [])` is a safe lookup: if the response has no such entry, you get an empty list instead of an error.

The `csv/` prefix contains two layouts of the same data:

- `csv/by_year/YYYY.csv`: every station, one year per file
- `csv/by_station/STATIONID.csv`: one station, every year in one file

The `parquet/` prefix contains the same data a third time, in a columnar format split by year and element. That is the copy the required notebooks read.

### Reading a size without reading the file

Every object carries its size as metadata:

```python
# RUNS ON: laptop (Positron)
resp = s3.list_objects_v2(Bucket=BUCKET, Prefix="csv/by_year/202")
for obj in resp["Contents"]:
    print(f"{obj['Key']:<28} {human(obj['Size'])}")
```

**What this code does.**

- `Prefix="csv/by_year/202"` narrows the listing to keys that *begin with* that text, which here means the files for 2020 onward. A prefix is a filter that S3 applies on its side, before it answers.
- Each item in `resp["Contents"]` describes one object. `obj["Key"]` is its name and `obj["Size"]` is its size in bytes.
- `{obj['Key']:<28}` pads the name to 28 characters so the sizes line up in a column.
- You learn that these files are over a gigabyte each, and you have downloaded none of them.

One listing call returns at most 1,000 objects. For larger prefixes, a *paginator* keeps asking until there are no more; the class notebooks' `prefix_size()` helper uses one.

### Reading a slice of a file

S3 supports range requests, so you can read the first few hundred bytes of a gigabyte file to see its shape:

```python
# RUNS ON: laptop (Positron)
obj = s3.get_object(Bucket=BUCKET, Key="csv/by_year/2024.csv", Range="bytes=0-299")
print(obj["Body"].read().decode())
```

**What this code does.**

- `get_object` is the request that actually fetches file contents. Without `Range` it would start sending the whole file.
- `Range="bytes=0-299"` asks for the first 300 bytes only.
- `obj["Body"]` is a *stream* that you read from. `.read()` pulls the bytes off it, and `.decode()` turns them into text.

Use this to check whether a file has a header row before you read it. Never assume either way; the check costs 300 bytes.

---

## 2. Three levers for data that does not fit

When data does not fit, there are three levers, and they all express one principle: **move the filter to the data instead of moving the data to the filter.**

**Lever 1: pick the right object.** GHCN offers the same data by year (over a gigabyte, all stations) and by station (a few megabytes, all years). If you need one location, read the station file. Choosing the object is the cheapest filter there is. Reading one Parquet year-and-element slice, as the class notebooks do, is the same lever.

**Lever 2: read fewer columns.** `usecols` (for CSV) or `columns` (for Parquet) tells pandas to discard columns while reading, so they never take memory.

**Lever 3: read fewer rows at a time.** `chunksize` returns an iterator of DataFrames; you filter each chunk and keep only what survives.

### One station, straight from S3

```python
# RUNS ON: laptop (Positron)
import pandas as pd

COLS = ["id", "date", "element", "value", "m_flag", "q_flag", "s_flag", "obs_time"]
STATION = "USC00047851"          # SAN LUIS OBISPO POLY, CA; records since 1893
key = f"csv/by_station/{STATION}.csv"

# Does the file have a header row? Read 100 bytes and look.
first = s3.get_object(Bucket=BUCKET, Key=key, Range="bytes=0-99")["Body"].read().decode()
has_header = first.upper().startswith("ID,")

obj = s3.get_object(Bucket=BUCKET, Key=key)
df = pd.read_csv(
    obj["Body"],
    header=0 if has_header else None,
    names=COLS,
    usecols=["id", "date", "element", "value", "q_flag"],     # lever 2
    dtype={"id": "string", "element": "string", "q_flag": "string"},
)
df = df[df["q_flag"].isna()]         # drop values that failed NOAA's quality checks
print(df.shape, human(df.memory_usage(deep=True).sum()))
```

**What this code does.**

- `key` builds the name of that station's file. This is **lever 1**: you chose the small object.
- The two lines after the comment read the first 100 bytes and set `has_header`.
- `pd.read_csv(obj["Body"], ...)` reads the table straight off the stream. Nothing is saved to your disk.
- `usecols=[...]` is **lever 2**: pandas discards the other columns as it parses.
- The quality-flag filter drops values that failed NOAA's checks, so they become missing rather than wrong.
- The last line prints the shape and the measured memory use.

### Filtering a large file in chunks

The 2024 by-year file holds every station in the world. The cell below reads only its **first 300 MB**, a million rows at a time, keeps the SLO rows, and reports how long that took. Expect a few minutes on a home connection. Do not run the cell twice while it is working.

```python
# RUNS ON: laptop (Positron)
import time

key = "csv/by_year/2024.csv"
first = s3.get_object(Bucket=BUCKET, Key=key, Range="bytes=0-99")["Body"].read().decode()
has_header = first.upper().startswith("ID,")

SAMPLE_BYTES = 300_000_000                          # the first 300 MB, not the whole file

t0 = time.perf_counter()
obj = s3.get_object(Bucket=BUCKET, Key=key, Range=f"bytes=0-{SAMPLE_BYTES - 1}")
chunks = pd.read_csv(
    obj["Body"],
    header=0 if has_header else None,
    names=COLS,
    usecols=["id", "date", "element", "value"],
    dtype={"id": "string", "element": "string"},
    chunksize=1_000_000,                            # lever 3
)
keep = pd.concat(c[c["id"] == STATION] for c in chunks)
seconds = time.perf_counter() - t0

print(f"{len(keep):,} rows for {STATION} in {seconds:,.0f} s, after reading {human(SAMPLE_BYTES)}")
```

**What this code does.**

- `Range=...` limits the read to the first 300 MB. The file is sorted by date, so that covers roughly January to mid-March.
- `chunksize=1_000_000` is **lever 3**. `pd.read_csv` returns an *iterator* that hands over one table of a million rows at a time.
- `pd.concat(c[c["id"] == STATION] for c in chunks)` keeps only the SLO rows from each chunk and stitches them together. Your memory holds one chunk at a time.
- The time printed is a **measurement of this 300 MB sample on your connection**. It is not an estimate for the whole file, and it should not be compared with a different job on a different machine.

Chunking protects your memory, not your time: every byte still travels to your laptop to be inspected. Compare the two cells. The by-station cell read a few megabytes and returned every SLO row since 1893. This one read 300 MB to find a few hundred. Lever 1 was the one that mattered.

### The units trap

GHCN stores temperatures in **tenths of a degree Celsius** and precipitation in **tenths of a millimeter**. A `TMAX` value of `266` means 26.6 °C. Divide by 10 before you do anything else.

```python
# RUNS ON: laptop (Positron)
df["date"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d")
tmax = df[df["element"] == "TMAX"].copy()
tmax["tmax_c"] = tmax["value"] / 10
```

---

## 3. Cost in more detail

Approximate prices for `us-east-1` at the time of writing. Check the pricing pages for current numbers.

### Storage

| What | Approx. price | What it means for you |
|---|---|---|
| S3 Standard storage | $0.023 per GB per month | The NOAA bucket is paid for by the AWS Open Data program, not by you. A bucket of your own is charged at this rate |
| S3 requests | Fractions of a cent per thousand | Every listing and metadata call in this module together: well under a cent |
| Data transfer, S3 to your laptop | A monthly free allowance, then about $0.09 per GB | For a public bucket like NOAA's, the bucket owner's program covers this. For data in your own bucket, large repeated downloads to a laptop add up |
| Data transfer, S3 to SageMaker in the same region | No charge | One reason to put the computer next to the data |
| SageMaker space disk | About $0.10 per GB per month | A stopped space with the default 5 GB: about 50 cents a month |

### Computing

| What | Approx. price | What it means for you |
|---|---|---|
| `ml.t3.medium` (2 vCPUs, 4 GB) | $0.05 per hour | A three-hour session: 15 cents |
| `ml.t3.xlarge` (4 vCPUs, 16 GB) | $0.20 per hour | Four times the memory for four times the price |
| `ml.m5.4xlarge` (16 vCPUs, 64 GB) | $0.92 per hour | A machine that could load a whole by-year CSV. An hour costs less than a coffee, a forgotten month costs hundreds of dollars |

Computing is rented in hours, not bought in years. If a job needs 64 GB of RAM once a quarter, you rent 64 GB for that hour. Larger instance types may not be available on every account plan; check before you plan around one.

### How you code is how you spend

| A choice you make | What it reduces | Which charge that is |
|---|---|---|
| Read one slice or one station file instead of a whole year (lever 1) | Bytes read | Time the instance is running; transfer, if the code runs outside the region |
| Read only the columns you need, or read in chunks (levers 2 and 3) | Memory the job needs | Instance size: the job fits on a small machine instead of a large one |
| Run the notebook in the same region as the bucket | Distance the data travels | Data transfer |
| Code that finishes in seconds instead of minutes | Hours the instance is running | Instance price per hour |
| Stopping the space when you finish | Hours the instance is running | Instance price per hour |

An analysis costs roughly (how much machine) × (how long it runs) + (how many bytes are stored or moved), and every lever above pushes one of those numbers down.

### Say it in your own words

1. In your own words, what are you paying for when a JupyterLab space is *Running*? What are you paying for when it is *Stopped*?
2. A colleague says, "The data doesn't fit in memory, so let's just rent the 64 GB machine." Explain what they should try first, and why that order saves money.
3. Pick one row of the "forgot to stop it" table in the reading. Describe what went wrong, what it cost, and the habit that prevents it.
4. Finish this sentence with a specific example: "Writing efficient code reduces cloud cost because ..."

## References

- GHCN-Daily by-year file format: <https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme-by_year.txt>
- pandas `read_csv` (`usecols`, `chunksize`): <https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html>
- S3 pricing: <https://aws.amazon.com/s3/pricing/>
- SageMaker AI pricing: <https://aws.amazon.com/sagemaker/ai/pricing/>
