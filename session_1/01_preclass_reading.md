---
title: "Pre-Class Reading: Data Bigger Than Your Laptop"
---

**GSB 5544 · Computing and Machine Learning for Business Analytics**

*Read before class. Run the code as you go; the practice activity assumes you have.*

---

## Why this matters for a business analyst

Every dataset you have used in this course so far arrived as a file you opened. That is not how data arrives in practice. The sales history, the clickstream, the sensor log, the claims table: they live somewhere else, they are usually larger than your machine, and someone has to decide *what to bring over* before any modeling begins.

That decision is an extraction problem, and it is the first place a business analyst runs into infrastructure. This reading gives you the three things you need to make that decision well:

1. A way to measure what your own machine can hold.
2. The vocabulary to describe the size of data and the parts of a cloud system.
3. A working pattern for reading only what you need from a large remote dataset.

We will use weather data as the example. Weather is one of the most common external covariates in business analytics: it drives beverage and apparel demand, energy load, insurance claims, delivery times, and foot traffic. It is also a dataset that is far too large to open on a laptop, which is exactly the point.

---

## 1. What your machine actually has

Your laptop has an amount of memory (RAM) installed, and a smaller amount that is *available right now*. The available number is the one that determines whether a dataset loads. Measure it:

```python
import psutil

vm = psutil.virtual_memory()
du = psutil.disk_usage("/")

print(f"Physical cores : {psutil.cpu_count(logical=False)}")
print(f"Logical cores  : {psutil.cpu_count(logical=True)}")
print(f"Total RAM      : {vm.total / 1e9:.1f} GB")
print(f"Available RAM  : {vm.available / 1e9:.1f} GB")   # the number that matters
print(f"Free disk      : {du.free / 1e9:.1f} GB")
```

Write your available RAM down. You will compare it to a file size later.

Two things people get wrong here:

- **Total is not available.** A 16 GB machine running a browser, Slack, and a notebook server often has 3–5 GB actually free.
- **Disk is not memory.** A 1 TB drive does not mean you can *analyze* 1 TB. pandas works in memory, and memory is the smaller number.

---

## 2. The units of data

You need to be fluent in these. Every size you will see in a cloud console, a bill, or an error message uses them.

| Unit | Bytes | Something that size |
|---|---|---|
| bit | 1/8 byte | One yes/no |
| byte (B) | 1 | One character |
| kilobyte (KB) | 1,000 | A paragraph |
| megabyte (MB) | 1,000,000 | A phone photo; a semester's worth of survey data |
| gigabyte (GB) | 1,000,000,000 | A year of daily weather readings, worldwide |
| terabyte (TB) | 1,000,000,000,000 | A large retailer's transaction history |
| petabyte (PB) | 1,000,000,000,000,000 | A web-scale crawl |

Two conventions coexist. Storage vendors and cloud consoles mostly use base 1000 (1 KB = 1,000 B). Operating systems and memory often use base 1024 (1 KiB = 1,024 B). This is why a "1 TB" drive shows as 931 GB in your file browser. Neither is wrong; you just need to know which one you are reading.

A helper you will use constantly:

```python
def human(n, base=1000):
    """Turn a byte count into a readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if n < base:
            return f"{n:,.1f} {unit}"
        n /= base
    return f"{n:,.1f} EB"

human(1_500_000)        # '1.5 MB'
human(1_336_457_184)    # '1.3 GB'
```

### File size is not memory size

A CSV that is 800 MB on disk will not be 800 MB in pandas. Text columns are stored as Python objects, each with overhead, and pandas commonly needs 2–5× the on-disk size to hold a mostly-text CSV. Check what a DataFrame really costs with:

```python
df.memory_usage(deep=True).sum()   # deep=True, or string columns are undercounted
```

So the question "does this fit?" is really: *is (file size × a multiplier) less than my available RAM?* When the answer is no, you do not need a bigger laptop. You need a smaller extraction.

---

## 3. The vocabulary of AWS

Amazon Web Services is the largest cloud provider, and its vocabulary has become the industry's vocabulary. Nine terms cover most of what you will read in documentation and error messages.

| Term | What it is | The confusion it prevents |
|---|---|---|
| **Region** | A geographic cluster of data centers (`us-east-1`, `us-west-2`) | Why a bucket "doesn't exist": you are looking in the wrong region |
| **S3** | Simple Storage Service. Object storage, not a filesystem | Why there are no real folders, only names that contain slashes |
| **Bucket** | A named container for objects. Names are globally unique across all of AWS | Why `my-data` is already taken by a stranger |
| **Object** | One stored item plus its metadata (size, last modified, type) | Why you can read an object's size without downloading it |
| **Key** | The object's full name within the bucket, e.g. `csv/by_year/2024.csv` | Why that is one string, not three folders and a file |
| **Prefix** | The start of a key, used to list "everything under" something | How S3 fakes folders |
| **EC2** | Elastic Compute Cloud. A rented virtual computer | What "compute" means as distinct from "storage" |
| **IAM** | Identity and Access Management. Who may do what | Why code gets `AccessDenied` even on public data |
| **Credentials** | The keys that identify you to AWS | Why "unsigned" or "anonymous" requests exist, and when you need to sign one |

The single most important idea underneath all nine: **storage and compute are separate.** Data sits in S3. Computers (your laptop, or a rented EC2 instance) reach into S3 for it. The data does not have to be where the computer is.

---

## 4. Reading from S3 without an account

Many large public datasets are hosted on S3 through the [Registry of Open Data on AWS](https://registry.opendata.aws/). They can be read *anonymously*: no account, no credit card, no credentials. The request is simply not signed.

Install what you need (once):

```bash
pip install boto3 s3fs psutil pandas matplotlib
```

`boto3` is the official AWS library for Python. Create an unsigned client:

```python
import boto3
from botocore import UNSIGNED
from botocore.config import Config

s3 = boto3.client("s3", region_name="us-east-1",
                  config=Config(signature_version=UNSIGNED))
```

Our dataset is NOAA's **Global Historical Climatology Network – Daily (GHCN-D)**: daily observations from tens of thousands of weather stations worldwide, some going back to the 1760s. It lives in the bucket `noaa-ghcn-pds`.

### Listing, not downloading

The first thing to do with any bucket is look at what is in it. `Delimiter="/"` asks S3 to group keys by their first path segment, which is how you see the "folders":

```python
BUCKET = "noaa-ghcn-pds"

resp = s3.list_objects_v2(Bucket=BUCKET, Delimiter="/")
print([p["Prefix"] for p in resp.get("CommonPrefixes", [])])
# ['csv.gz/', 'csv/', 'parquet/']

print([o["Key"] for o in resp.get("Contents", [])][:6])
# ['ghcnd-countries.txt', 'ghcnd-inventory.txt', 'ghcnd-states.txt', 'ghcnd-stations.txt', ...]
```

The `csv/` prefix contains two layouts of the same data:

- `csv/by_year/YYYY.csv` — every station, one year per file
- `csv/by_station/STATIONID.csv` — one station, every year in one file

### Reading a size without reading the file

Every object carries its size as metadata. You can read it for free:

```python
resp = s3.list_objects_v2(Bucket=BUCKET, Prefix="csv/by_year/202")
for obj in resp["Contents"]:
    print(f"{obj['Key']:<28} {human(obj['Size'])}")
```

```
csv/by_year/2020.csv         1.3 GB
csv/by_year/2021.csv         1.4 GB
csv/by_year/2022.csv         1.4 GB
csv/by_year/2023.csv         1.4 GB
csv/by_year/2024.csv         1.3 GB
csv/by_year/2025.csv         1.3 GB
csv/by_year/2026.csv         818.8 MB
```

Compare that to your available RAM from section 1, and remember the multiplier. One year of GHCN is a file most laptops cannot open with a plain `pd.read_csv`.

For a single object, `head_object` returns the metadata alone:

```python
meta = s3.head_object(Bucket=BUCKET, Key="csv/by_year/2024.csv")
meta["ContentLength"], meta["LastModified"]
```

### Reading a *slice* of a file

S3 supports HTTP range requests, so you can read the first few hundred bytes of a gigabyte file to see its shape:

```python
obj = s3.get_object(Bucket=BUCKET, Key="csv/by_year/2024.csv", Range="bytes=0-299")
print(obj["Body"].read().decode())
```

Use this to check whether a file has a header row before you read it. If the first line begins with `ID,`, it does.

---

## 5. Extraction strategy: filter at the source

When data does not fit, there are three levers, and they all express one principle: **move the filter to the data instead of moving the data to the filter.**

**Lever 1: pick the right object.** GHCN offers the same data by year (1.3 GB, all stations) and by station (a few MB, all years). If you need one location, read the station file. Choosing the object is the cheapest filter there is.

**Lever 2: read fewer columns.** `usecols` tells pandas to discard columns while parsing, so they never take memory.

**Lever 3: read fewer rows at a time.** `chunksize` returns an iterator of DataFrames; you filter each chunk and keep only what survives.

Here is the pattern, reading one station directly from S3. The GHCN CSV columns are, in order: station ID, date (YYYYMMDD), element code, value, and four flag columns.

```python
import pandas as pd

COLS = ["id", "date", "element", "value", "m_flag", "q_flag", "s_flag", "obs_time"]
STATION = "USC00047851"          # SAN LUIS OBISPO POLY, CA — records since 1893
key = f"csv/by_station/{STATION}.csv"

# Does the file have a header row? Read 100 bytes and look.
first = s3.get_object(Bucket=BUCKET, Key=key, Range="bytes=0-99")["Body"].read().decode()
has_header = first.upper().startswith("ID,")

obj = s3.get_object(Bucket=BUCKET, Key=key)
df = pd.read_csv(
    obj["Body"],
    header=0 if has_header else None,
    names=COLS,
    usecols=["id", "date", "element", "value"],     # lever 2
    dtype={"id": "string", "element": "string"},
)
df.shape
```

For a by-year file, add lever 3 and keep only the rows you want as they stream past:

```python
key = "csv/by_year/2024.csv"
first = s3.get_object(Bucket=BUCKET, Key=key, Range="bytes=0-99")["Body"].read().decode()
has_header = first.upper().startswith("ID,")

chunks = pd.read_csv(
    f"s3://{BUCKET}/{key}",
    storage_options={"anon": True},                 # unsigned, via s3fs
    header=0 if has_header else None,
    names=COLS,
    usecols=["id", "date", "element", "value"],
    chunksize=1_000_000,                            # lever 3
)
keep = pd.concat(c[c["id"] == STATION] for c in chunks)
```

Both produce the same rows for that station. One reads 6.7 MB; the other reads 1.3 GB and throws almost all of it away. Lever 1 was the one that mattered.

### The units trap

GHCN stores temperatures in **tenths of a degree Celsius** and precipitation in **tenths of a millimeter**. A `TMAX` value of `266` means 26.6 °C. Divide by 10 before you do anything else, or your first chart will show 300-degree days. Data arrives with conventions attached; reading the documentation is part of extraction.

```python
df["date"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d")
tmax = df[df["element"] == "TMAX"].copy()
tmax["tmax_c"] = tmax["value"] / 10
```

---

## 6. Where this goes next

In class you will:

- Measure your own machine and put the class's numbers side by side.
- Read sizes from the GHCN bucket and decide, with arithmetic, what fits.
- Extract one station's history, transform it, and plot it.
- Compare two markets' weather histories the way an analyst would before building a demand model.

Everything in the practice activity uses only what is on this page.

---

## Reading check

Answer these for yourself before class. They are the first questions in the practice activity.

1. Your machine reports 16 GB total and 4.2 GB available. A CSV is 1.3 GB on disk. Will `pd.read_csv` on the whole file probably succeed? Show the arithmetic.
2. What is the difference between a bucket, a key, and a prefix? Give one example of each from `noaa-ghcn-pds`.
3. Why can `list_objects_v2` tell you a file's size without downloading it?
4. You need every temperature reading for Phoenix since 1990. Which object do you read: `csv/by_year/*.csv` or `csv/by_station/USW00023183.csv`? Why?
5. A `TMAX` value in the file is `412`. What is the temperature in Celsius? In Fahrenheit?

---

## References

- Registry of Open Data on AWS — NOAA GHCN-D: https://registry.opendata.aws/noaa-ghcn/
- GHCN-D by-year file format (column order and units): https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme-by_year.txt
- GHCN-D full readme (element codes, flags): https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt
- boto3 S3 client reference: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
- pandas `read_csv` (`usecols`, `chunksize`, `storage_options`): https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
