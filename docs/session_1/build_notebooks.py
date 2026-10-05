"""
Builds four notebooks from one source of truth:
  02_topics_of_practice.ipynb            (fill-in-the-blank: ⟦...⟧ -> ____)
  02_topics_of_practice_SOLUTIONS.ipynb
  03_practice_activity.ipynb             (answer cells emptied)
  03_practice_activity_SOLUTIONS.ipynb

Conventions
  ⟦...⟧     text that becomes a blank (____) in the student version
  answer()  a code cell that is emptied in the student version; its
            "# RUNS ON:" first line is kept so students still see where it runs
  Every code cell's source begins with one of exactly three lines:
      # RUNS ON: laptop
      # RUNS ON: SageMaker ml.t3.medium (us-east-1)
      # RUNS ON: Athena fleet (results land in S3)
  build() refuses to write a notebook where any code cell lacks one, and
  compiles every solution cell (IPython %/! lines are stripped before compiling).
"""
import re
import nbformat as nbf

BLANK = "____"
RUNS_ON = "# RUNS ON:"
RUNS_ON_VALUES = {
    "# RUNS ON: laptop",
    "# RUNS ON: SageMaker ml.t3.medium (us-east-1)",
    "# RUNS ON: Athena fleet (results land in S3)",
}


def md(src):
    return ("md", src.strip("\n"))


def code(src):
    return ("code", src.strip("\n"))


def answer(src):
    """A code cell that is fully hidden in the student version."""
    return ("answer", src.strip("\n"))


def build(cells, path, student):
    nb = nbf.v4.new_notebook()
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    out = []
    for kind, src in cells:
        if kind == "md":
            out.append(nbf.v4.new_markdown_cell(src))
        elif kind == "code":
            if student:
                src = re.sub(r"⟦.*?⟧", BLANK, src, flags=re.S)
            else:
                src = re.sub(r"⟦(.*?)⟧", r"\1", src, flags=re.S)
            out.append(nbf.v4.new_code_cell(src))
        elif kind == "answer":
            if student:
                first = src.splitlines()[0]
                src = first + "\n# your code here\n"
            out.append(nbf.v4.new_code_cell(src))
    nb.cells = out

    # sanity 1: every code cell says where it runs
    for c in nb.cells:
        if c.cell_type == "code":
            first = c.source.splitlines()[0] if c.source else ""
            if first not in RUNS_ON_VALUES:
                raise SystemExit(f"{path}: code cell without a valid RUNS ON line:\n{c.source[:120]}")

    # sanity 2: every code cell in the solutions version must compile
    if not student:
        for c in nb.cells:
            if c.cell_type == "code":
                plain = "\n".join(l for l in c.source.splitlines() if not l.lstrip().startswith(("%", "!")))
                compile(plain, path, "exec")

    nbf.write(nb, path)


# ======================================================================
# NOTEBOOK 2 — Topics of practice (fill in the blanks)
# ======================================================================
nb2 = [
md("""
# Topics of Practice: Data Bigger Than Your Laptop

**GSB 5544 · Computing and Machine Learning for Business Analytics**

This notebook walks through the main functions from the pre-class reading, one short block at a time. Each block names the section of the reading it draws on. Replace every `____` with the right code and run the cell.

**Run this notebook inside your SageMaker Studio JupyterLab space** (reading, §4), not on your laptop. Every code cell begins with a `# RUNS ON:` line that says where it executes. Read it before you press Shift-Enter; the point of today is to notice where the work happens.

Bring the five laptop numbers you wrote down from the reading, §1. Block A needs them.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
%pip install -q s3fs             # harmless if already present

import io
import time
import psutil
import boto3
import pandas as pd
import matplotlib.pyplot as plt
from botocore import UNSIGNED
from botocore.config import Config

BUCKET = "noaa-ghcn-pds"
REGION = "us-east-1"             # the bucket's region; this instance is in it too
"""),

# ---------------------------------------------------------------- Start here
md("""
## Start here: what stores, what computes

Four things take part today. Keep two questions apart for each one: **does it store data?** and **does it run code?**

| | What it is | Stores data? | Runs code? | What you pay for |
|---|---|---|---|---|
| **Your computer** | The laptop in front of you | Yes, on its disk | Yes, with its own CPU and RAM | Nothing extra |
| **SageMaker space** | A computer you rent in an AWS data center. Ours has 2 cores, 4 GB of RAM, and a 5 GB disk | A little: notebooks and small files | Yes, with *its* CPU and RAM, not yours | Every hour it is *Running* |
| **S3 bucket** | Cloud storage. Files kept in AWS, readable from your computer or from SageMaker | Yes, as much as you like | **No.** It can only hand over bytes | Every GB stored, per month |
| **Athena** | A query service. AWS's machines run your SQL over files that sit in S3 | No. It reads from S3 and writes its answer back to S3 | Yes, SQL only, on AWS's machines | Every byte it scans |

**Storing is not processing.** Data in S3 does nothing until some computer reads it. The question is always *which* computer: yours, your SageMaker space, or Athena's. The bytes travel to wherever the code runs, and they must fit in **that** machine's RAM.

**Disk is not RAM.** Disk keeps files when the machine is off. RAM is the working space a running program uses, and it is much smaller. A file can fit on a disk and still be too big to open.

**Check your own computer.** You need two numbers, RAM and free disk:

- **Mac:** Apple menu → *About This Mac* shows memory. *System Settings → General → Storage* shows free disk.
- **Windows:** Ctrl+Shift+Esc → *Performance → Memory* shows RAM. *Settings → System → Storage* shows free disk.
- **Or in Python on your laptop** (a notebook opened on your laptop, not this one):

```python
# RUNS ON: laptop
import psutil
print("RAM (GB):      ", round(psutil.virtual_memory().total / 1e9, 1))
print("Free disk (GB):", round(psutil.disk_usage("/").free / 1e9, 1))
```

That block is text, not a cell, on purpose. If you ran it here it would report the SageMaker machine, because that is where this notebook's code runs.

Fill in each blank with `laptop`, `SageMaker`, `S3`, or `Athena`.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
where = {
    "Stores the 1.3 GB weather file we use today":         "⟦S3⟧",
    "Runs the cells of this notebook":                     "⟦SageMaker⟧",
    "Shows you this notebook in a browser tab":            "⟦laptop⟧",
    "Runs a SQL WHERE clause over files stored in S3":     "⟦Athena⟧",
    "Can store data but cannot run any code":              "⟦S3⟧",
    "Bills by the hour while Running, even if you are idle": "⟦SageMaker⟧",
}

expected = ["s3", "sagemaker", "laptop", "athena", "s3", "sagemaker"]
given = [v.strip().lower() for v in where.values()]
wrong = [q for q, g, e in zip(where, given, expected) if g != e]
print("All correct" if not wrong else "Check these: " + "; ".join(wrong))
"""),

# ---------------------------------------------------------------- A
md("""
## A. Two machines, side by side

*From the reading, §1 and §4.* You ran the `psutil` cell on your laptop before class. Now run it again: this kernel lives on a rented `ml.t3.medium` in `us-east-1`, and your laptop is a browser tab.

Fill in the call that reports memory and the attribute that gives the memory available **right now**.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
vm = psutil.⟦virtual_memory⟧()
du = psutil.disk_usage("/")

sagemaker = {
    "physical cores":     psutil.cpu_count(logical=False),
    "logical cores":      psutil.cpu_count(logical=True),
    "total RAM (GB)":     round(vm.total / 1e9, 1),
    "available RAM (GB)": round(vm.⟦available⟧ / 1e9, 1),
    "free disk (GB)":     round(du.free / 1e9, 1),
}
MY_RAM = vm.⟦available⟧          # available RAM of the machine running THIS cell; we compare file sizes against it below
sagemaker
"""),

md("""
Now paste your laptop's numbers into the dictionary and build the comparison. Fill in the dictionary that holds this machine's numbers.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
laptop = {                        # <- replace every value with the number you wrote down from the reading, §1
    "physical cores":     0,
    "logical cores":      0,
    "total RAM (GB)":     0.0,
    "available RAM (GB)": 0.0,
    "free disk (GB)":     0.0,
}

compare = pd.DataFrame({"laptop": laptop, "SageMaker ml.t3.medium": ⟦sagemaker⟧})
compare["SageMaker ÷ laptop"] = (compare["SageMaker ml.t3.medium"] / compare["laptop"]).round(2)
compare
"""),

md("""
**Check yourself.** The rented machine is probably *smaller* than your laptop. So why rent it at all? Answer in one sentence, as a comment.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
# ⟦Because it sits in the same region as the data: reads are fast and free, and it is the same machine for everyone. What changed is location, not size; size is one dropdown away if we need it.⟧
"""),

# ---------------------------------------------------------------- B
md("""
## B. The units of data

*From the reading, §2.* Byte counts are unreadable past a few million. Write the helper that turns them into KB / MB / GB and so on, using base 1000.

Fill in the list of units in ascending order and the line that steps `n` down one unit.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
def human(n, base=1000):
    for unit in [⟦"B", "KB", "MB", "GB", "TB", "PB"⟧]:
        if n < base:
            return f"{n:,.1f} {unit}"
        n ⟦/= base⟧
    return f"{n:,.1f} EB"

print(human(1_500_000))          # expect 1.5 MB
print(human(1_336_457_184))      # expect 1.3 GB
print(human(MY_RAM))             # this machine's available RAM, readable
"""),

md("""
**Check yourself.** A "1 TB" drive shows as 931 GB in your file browser. Which base does the drive maker use, and which does the operating system use? Write your answer in the cell below as a comment.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
# Drive maker uses base ⟦1000⟧; the OS uses base ⟦1024⟧.
# 1e12 / 1024**3 = ⟦931.3⟧ GiB, which the OS labels "GB".
"""),

# ---------------------------------------------------------------- C
md("""
## C. The vocabulary of AWS

*From the reading, §3.* Fill in the term that each definition describes. The cell checks your answers.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
vocab = {
    "A named container for objects; its name is globally unique":            "⟦bucket⟧",
    "One stored item plus its metadata such as size":                         "⟦object⟧",
    "The full name of an object inside its bucket":                           "⟦key⟧",
    "The start of a key, used to list everything 'under' something":          "⟦prefix⟧",
    "A geographic cluster of data centers such as us-east-1":                 "⟦region⟧",
    "A rented virtual computer":                                              "⟦EC2⟧",
    "The size of a rented computer: cores, RAM, and a price per hour":        "⟦instance type⟧",
    "A SQL engine that scans files in S3 across many machines, billed per byte": "⟦Athena⟧",
    "The service that decides who may do what":                               "⟦IAM⟧",
}

expected = {"bucket", "object", "key", "prefix", "region", "ec2", "instance type", "athena", "iam"}
given = {v.strip().lower() for v in vocab.values()}
print("All correct" if given == expected else f"Check: {expected - given}")
"""),

# ---------------------------------------------------------------- D
md("""
## D. Connect without an account

*From the reading, §5.* Public datasets on S3 can be read with an **unsigned** request. Build the client, then list the top-level "folders" of the GHCN bucket.

This machine *has* AWS credentials (it is inside your lab account), but an unsigned request does not use them. The public bucket does not care who is asking.

Fill in the signature setting that makes the request anonymous, and the delimiter that makes S3 group keys like folders.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
s3 = boto3.client(
    "s3",
    region_name=REGION,
    config=Config(signature_version=⟦UNSIGNED⟧),
)

resp = s3.list_objects_v2(Bucket=BUCKET, Delimiter=⟦"/"⟧)

print("Prefixes :", [p["Prefix"] for p in resp.get("⟦CommonPrefixes⟧", [])])
print("Files    :", [o["Key"] for o in resp.get("Contents", [])][:6])
"""),

md("""
Look at the output. `csv/` is not a folder. In one sentence, what is it? Type your answer as a comment.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
# ⟦It is a prefix: the shared beginning of many object keys. S3 groups keys by it when asked, which looks like a folder.⟧
"""),

# ---------------------------------------------------------------- E
md("""
## E. Read a size without reading the file

*From the reading, §5.* Every object carries its size as metadata. List the by-year files for the 2020s and print each size in readable units.

Fill in the prefix that selects `csv/by_year/2020.csv` through `2026.csv`, and the field that holds an object's size.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=⟦"csv/by_year/202"⟧)

sizes = {}
for obj in resp["Contents"]:
    sizes[obj["Key"]] = obj[⟦"Size"⟧]
    print(f"{obj['Key']:<28} {human(obj[⟦'Size'⟧])}")

BY_YEAR_2024_BYTES = sizes["csv/by_year/2024.csv"]     # keep; block J compares against it
"""),

md("""
Now the comparison that the whole reading builds toward. pandas typically needs about **3×** a text CSV's size in memory. For each file, decide whether a plain `pd.read_csv` would fit in **this machine's** available RAM. (Renting a machine did not change the arithmetic.)

Fill in the multiplier and the comparison.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
MULT = ⟦3⟧

for key, size in sizes.items():
    need = size * MULT
    fits = need ⟦<⟧ MY_RAM
    print(f"{key:<28} needs ~{human(need):>9}   fits on this ml.t3.medium: {fits}")
"""),

# ---------------------------------------------------------------- F
md("""
## F. Peek at a file with a range request

*From the reading, §5.* You can read the first few hundred bytes of a gigabyte file to see its shape. Do that for the 2024 by-year file and check whether it has a header row. Never assume either way.

Fill in the `Range` header for the first 300 bytes.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
key = "csv/by_year/2024.csv"

obj = s3.get_object(Bucket=BUCKET, Key=key, Range=⟦"bytes=0-299"⟧)
first = obj["Body"].read().decode()
print(first)

has_header = first.upper().startswith(⟦"ID,"⟧)
print("Header row present:", has_header)
"""),

# ---------------------------------------------------------------- G
md("""
## G. Extract one station, not one year

*From the reading, §6.* Lever 1 is picking the right object. The Cal Poly station (`USC00047851`, SAN LUIS OBISPO POLY) has records since 1893 in a single file of about 7 MB. Read it, keeping only the four columns you need. The bytes travel from S3 to this instance over AWS's own network; nothing reaches your laptop except the printed output.

Fill in the station key, the header logic, and the `usecols` list.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
COLS = ["id", "date", "element", "value", "m_flag", "q_flag", "s_flag", "obs_time"]
STATION = "USC00047851"
key = f"csv/by_station/{⟦STATION⟧}.csv"

# size first, always
print("Size:", human(s3.head_object(Bucket=BUCKET, Key=key)["ContentLength"]))

# header check
first = s3.get_object(Bucket=BUCKET, Key=key, Range="bytes=0-99")["Body"].read().decode()
has_header = first.upper().startswith("ID,")

raw = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
df = pd.read_csv(
    io.BytesIO(raw),
    header=⟦0 if has_header else None⟧,
    names=COLS,
    usecols=⟦["id", "date", "element", "value"]⟧,
    dtype={"id": "string", "element": "string"},
)

print(df.shape)
print("In memory:", human(df.memory_usage(deep=⟦True⟧).sum()))
df.head()
"""),

# ---------------------------------------------------------------- H
md("""
## H. Transform

*From the reading, §6, "The units trap".* Dates are stored as `YYYYMMDD` integers and temperatures in tenths of a degree Celsius. Fix both, keep only daily maximum temperature, and compute a yearly mean.

Fill in the date format string, the element code, the unit conversion, and the resampling rule for year-end.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
df["date"] = pd.to_datetime(df["date"].astype(str), format=⟦"%Y%m%d"⟧)

tmax = df[df["element"] == ⟦"TMAX"⟧].copy()
tmax["tmax_c"] = tmax["value"] ⟦/ 10⟧

yearly = (
    tmax.set_index("date")["tmax_c"]
        .resample(⟦"YE"⟧)          # "Y" on pandas < 2.2
        .mean()
)

print(f"{len(tmax):,} TMAX readings, {yearly.index.min().year}–{yearly.index.max().year}")
yearly.tail()
"""),

# ---------------------------------------------------------------- I
md("""
## I. Bring the visual

*From the reading, §7.* One picture that came from a bucket you never downloaded, drawn on a machine you do not own.

Fill in the series to plot and the y-axis label with its unit.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
fig, ax = plt.subplots(figsize=(9, 4))
ax.plot(yearly.index, ⟦yearly.values⟧, linewidth=1.2)
ax.set_ylabel(⟦"Mean daily maximum (°C)"⟧)
ax.set_title(f"{STATION}: yearly mean of daily maximum temperature")
ax.grid(alpha=0.3)
plt.tight_layout()
plt.show()
"""),

# ---------------------------------------------------------------- J
md("""
## J. Ask Athena for the same station

*From the reading, §6, "the fourth lever".* So far every filter has run on the machine holding this kernel. Athena runs the filter on AWS's fleet, against the Parquet copy of the data, and hands back only the matching rows. Four cells: a results bucket you own, two helper functions, a table definition, and the query.

**Before you run this block:** blocks A–I must have run in this kernel (`REGION`, `STATION`, `human`, and `BY_YEAR_2024_BYTES` come from them), and your Studio role needs the Athena and S3 permissions from the reading, §4 part F. If the first cell stops with `AccessDeniedException`, that step is what is missing; the reading's §6 lists the other common errors. Every cell here is safe to run twice.

**Results bucket.** Athena writes every result to S3, so you need a bucket of your own. These clients are *signed*: they act as you, because this bucket is yours, not public. Fill in the bucket name in the create call.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
sts     = boto3.client("sts",    region_name=REGION)
athena  = boto3.client("athena", region_name=REGION)
s3_mine = boto3.client("s3",     region_name=REGION)

ACCOUNT        = sts.get_caller_identity()["Account"]
RESULTS_BUCKET = f"gsb5544-athena-{ACCOUNT}"     # bucket names are global, so include your account id
RESULTS        = f"s3://{RESULTS_BUCKET}/athena/"

s3_mine.create_bucket(Bucket=⟦RESULTS_BUCKET⟧)   # in us-east-1 no LocationConstraint is needed
print("Results will land in", RESULTS)
"""),

md("""
**A helper and a table.** `run_athena` starts a query, waits for it, and returns the query id plus Athena's statistics, which include the bytes scanned. The table definition tells Athena where the Parquet files are and how the `YEAR=`/`ELEMENT=` key layout maps to columns; nothing is copied, and DDL statements are free. Note the backticks around `date`: it is a reserved word in SQL.

Fill in the `boto3` call that starts a query.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
ATHENA_BYTES = 0                                  # running total of everything scanned today; block K audits it

def run_athena(sql, database=None):
    \"\"\"Start a query, wait for it, return (query id, statistics).\"\"\"
    global ATHENA_BYTES
    kwargs = {"QueryString": sql, "ResultConfiguration": {"OutputLocation": RESULTS}}
    if database:
        kwargs["QueryExecutionContext"] = {"Database": database}
    qid = athena.⟦start_query_execution⟧(**kwargs)["QueryExecutionId"]
    while True:
        q = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]
        state = q["Status"]["State"]
        if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(1)
    if state != "SUCCEEDED":
        raise RuntimeError(q["Status"].get("StateChangeReason", state))
    ATHENA_BYTES += q["Statistics"].get("DataScannedInBytes", 0)
    return qid, q["Statistics"]


def athena_df(qid):
    \"\"\"Read a finished query's result CSV from the results bucket.\"\"\"
    obj = s3_mine.get_object(Bucket=RESULTS_BUCKET, Key=f"athena/{qid}.csv")
    return pd.read_csv(io.BytesIO(obj["Body"].read()))
"""),

code("""
# RUNS ON: Athena fleet (results land in S3)
run_athena("CREATE DATABASE IF NOT EXISTS gsb5544")

DDL = '''
CREATE EXTERNAL TABLE IF NOT EXISTS gsb5544.ghcn (
    id         string,
    `date`     string,
    data_value bigint,
    m_flag     string,
    q_flag     string,
    s_flag     string,
    obs_time   string
)
PARTITIONED BY (year int, element string)
STORED AS PARQUET
LOCATION 's3://noaa-ghcn-pds/parquet/by_year/'
TBLPROPERTIES (
    'projection.enabled'        = 'true',
    'projection.year.type'      = 'integer',
    'projection.year.range'     = '1750,2030',
    'projection.element.type'   = 'enum',
    'projection.element.values' = 'TMAX,TMIN,PRCP,SNOW,SNWD,TAVG',
    'storage.location.template' = 's3://noaa-ghcn-pds/parquet/by_year/YEAR=${year}/ELEMENT=${element}/'
)
'''
run_athena(DDL, database="gsb5544")
print("Table gsb5544.ghcn is defined. Bytes scanned so far:", human(ATHENA_BYTES))
"""),

md("""
**The query.** Ask for the same station you pulled in block G, but only 2024 and only `TMAX` and `PRCP`. The `WHERE` clause is the extraction. Fill in the year and the name of the statistic that reports bytes scanned.
"""),

code("""
# RUNS ON: Athena fleet (results land in S3)
SQL = f'''
SELECT id, "date", data_value
FROM   gsb5544.ghcn
WHERE  year = ⟦2024⟧
  AND  element IN ('TMAX', 'PRCP')
  AND  id = '{STATION}'
'''

qid, stats = run_athena(SQL, database="gsb5544")
scanned = stats["⟦DataScannedInBytes⟧"]
station_2024 = athena_df(qid)

print(f"Rows returned : {len(station_2024):,}")
print(f"Bytes scanned : {human(scanned)}")
print(f"Query time    : {stats['TotalExecutionTimeInMillis'] / 1000:.1f} s")
print(f"Cost          : ${max(scanned, 10_000_000) / 1e12 * 5:.4f}   ($5 per TB, 10 MB minimum)")
print(f"2024 CSV was  : {human(BY_YEAR_2024_BYTES)}  ({BY_YEAR_2024_BYTES / scanned:.0f}× more bytes than Athena scanned)")
station_2024.head()
"""),

md("""
Athena scanned a fraction of the 1.3 GB by-year CSV from block E and returned only this station's rows, in seconds. Which lever from the reading did the `YEAR=`/`ELEMENT=` key layout let Athena pull? One sentence, as a comment.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
# ⟦Lever 1, choose the right object: the partition layout let Athena open only the 2024 TMAX and PRCP files and skip every other year and element before reading a single row.⟧
"""),

# ---------------------------------------------------------------- K
md("""
## K. Stop the meter

*From the reading, §7.* A session on a rented machine ends the same way every time. First, empty the results bucket from here. Fill in the call that lists the bucket and the call that deletes a batch of objects.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
listing = s3_mine.⟦list_objects_v2⟧(Bucket=RESULTS_BUCKET)
objects = listing.get("Contents", [])
print(f"{len(objects)} result objects, {human(sum(o['Size'] for o in objects))}")

if objects:
    s3_mine.⟦delete_objects⟧(Bucket=RESULTS_BUCKET, Delete={"Objects": [{"Key": o["Key"]} for o in objects]})

print("Bucket empty :", "Contents" not in s3_mine.list_objects_v2(Bucket=RESULTS_BUCKET))
print("Athena today :", human(ATHENA_BYTES), f"scanned, about ${max(ATHENA_BYTES, 10_000_000) / 1e12 * 5:.4f}")
"""),

md("""
Second, stop the instance. A cell cannot stop the machine it is running on without killing itself, so this part happens in the Studio window. In this order:

- [ ] File → Save All. Download anything you want to keep.
- [ ] In Studio, open **JupyterLab spaces**, find `gsb5544`, click **Stop**, and wait until the status reads *Stopped*.
- [ ] Read **Credits remaining** on Console Home (Learner Lab: the budget at the top of the lab page). Today should have cost well under a dollar.
- [ ] Learner Lab only: click **End Lab**.

Before you do, write one sentence, as a comment, that answers: *why did reading the station file work when reading the year file would not have, and what did Athena add on top of that?*
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
# ⟦The station file holds only the rows I needed, about 7 MB; the year file holds every station on Earth, 1.3 GB, and I would have thrown almost all of it away. Choosing the object was the filter. Athena moved that filter off my machine entirely: the fleet read the slice and I received only the answer.⟧
"""),
]

# ======================================================================
# NOTEBOOK 3 — Practice activity (empty cells)
# ======================================================================
nb3 = [
md("""
# Practice Activity: Weather as a Business Covariate

**GSB 5544 · Computing and Machine Learning for Business Analytics**

You manage inventory planning for a beverage distributor with two markets: **San Luis Obispo, CA** and **Phoenix, AZ**. Before anyone builds a demand model, you need each market's weather history, and it lives in a bucket that is far larger than your laptop.

**Run this notebook inside your SageMaker Studio JupyterLab space.** Every code cell begins with a `# RUNS ON:` line that says where it executes. Everything you need is in the pre-class reading and the topics-of-practice notebook. Each question has a code cell; some also ask for a short written answer in a markdown cell. Q1 and Q11 need numbers you wrote down from the reading.

**Stations**

| Market | Station ID | Name |
|---|---|---|
| San Luis Obispo | `USC00047851` | SAN LUIS OBISPO POLY, CA |
| Phoenix | `USW00023183` | PHOENIX AIRPORT, AZ |

Run the first setup cell, then do **Part 1**, a short guided trip from the cloud to your laptop. Part 2 (the Athena setup cell and Q1 to Q13) follows it.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
%pip install -q s3fs             # harmless if already present

import io
import json
import time
import datetime as dt
import psutil
import boto3
import pandas as pd
import matplotlib.pyplot as plt
from botocore import UNSIGNED
from botocore.config import Config

BUCKET   = "noaa-ghcn-pds"
REGION   = "us-east-1"
COLS     = ["id", "date", "element", "value", "m_flag", "q_flag", "s_flag", "obs_time"]
STATIONS = {"San Luis Obispo": "USC00047851", "Phoenix": "USW00023183"}

# unsigned: the public bucket does not care who is asking
s3 = boto3.client("s3", region_name=REGION, config=Config(signature_version=UNSIGNED))


def human(n, base=1000):
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if n < base:
            return f"{n:,.1f} {unit}"
        n /= base
    return f"{n:,.1f} EB"
"""),

# ---------------------------------------------------------------- Part 1
md("""
## Part 1 · Guided workflow: from the cloud to your laptop

A full year of daily high temperatures for every weather station on Earth is 4.4 million rows. You will let a cloud machine read and shrink it, then carry the small result home and chart it on your own computer. Nothing here uses Athena or creates a bucket.

| Step | Where the code runs | Where the data is stored |
|---|---|---|
| 1. Sign in and open your space | nowhere yet | S3 (NOAA's public bucket) |
| 2. Read and summarize | **SageMaker** instance | S3 → SageMaker RAM → SageMaker disk |
| 3. Download the summary | no code; your browser copies a file | SageMaker disk → **your laptop's** disk |
| 4. Read and chart | **your laptop** | laptop disk → laptop RAM |
| 5. Save and stop | nowhere | your work stays on the SageMaker disk and your laptop |

### Step 1. Sign in and open your SageMaker space

*Code runs: nowhere yet. Data is stored: in S3.*

1. Go to [console.aws.amazon.com](https://console.aws.amazon.com) and sign in as **root user** with the email and password of the account you already created.
2. Check that the region, top right, reads **N. Virginia**.
3. Search for **SageMaker AI** and open it. In the left menu choose **SageMaker Studio**, then **Open Studio**.
4. In Studio click **JupyterLab**, then click `gsb5544` in the spaces table. Click **Run space**, wait for the status to read *Running*, then click **Open JupyterLab**. The meter is now on.
5. Upload this notebook with the upload arrow in the file browser, open it, and run the first setup cell above.

### Step 2. Read from S3 and summarize, on the cloud machine

*Code runs: on the SageMaker instance. Data is stored: in S3, then in this instance's RAM, then as a small file on this instance's disk.*

First, prove to yourself which machine this is.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
import socket
print("This code is running on:", socket.gethostname())
print("RAM on this machine    :", round(psutil.virtual_memory().total / 1e9, 1), "GB")
"""),

md("""
Now read every station's 2024 daily highs straight from S3, keep California, and reduce it to one row per day. Fill in the three blanks.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
t0 = time.perf_counter()
raw = pd.read_parquet(
    "s3://noaa-ghcn-pds/parquet/by_year/YEAR=2024/ELEMENT=TMAX/",
    columns=["ID", "DATE", "DATA_VALUE"],          # read only the columns we need
    storage_options={"anon": ⟦True⟧},              # unsigned: the bucket is public
)
print(f"Read {len(raw):,} rows from S3 in {time.perf_counter() - t0:.0f} s")
print(f"They occupy {human(raw.memory_usage(deep=True).sum())} of this machine's RAM")

ca = raw[raw["ID"].str.startswith("USC0004")].copy()          # California cooperative stations
ca["date"]   = pd.to_datetime(ca["DATE"].astype(str), format="%Y%m%d")
ca["tmax_c"] = ca["DATA_VALUE"] / ⟦10⟧                        # stored in tenths of a degree C

summary = (ca.groupby(⟦"date"⟧)["tmax_c"]
             .agg(stations="count", coolest="min", average="mean", hottest="max")
             .round(1)
             .reset_index())

summary.to_csv("ca_tmax_2024_daily.csv", index=False)          # written to THIS machine's disk
print(f"Summary: {len(summary)} rows, saved to the SageMaker disk")
summary.head()
"""),

md("""
You should see about 4.4 million rows read in a few seconds and a summary of 366 rows. The big table lives only in this machine's RAM and disappears when the space stops. The small file is on this machine's disk.

### Step 3. Download the small file to your computer

*Code runs: none. Data is stored: on the SageMaker disk, and after this step also on your laptop's disk.*

1. In the file browser on the left, click the refresh arrow. `ca_tmax_2024_daily.csv` appears next to this notebook.
2. Right-click it and choose **Download**. It lands in your laptop's Downloads folder. It is about 11 KB.

### Step 4. Read it and chart it, on your own computer

*Code runs: on your laptop. Data is stored: on your laptop's disk, then in your laptop's RAM.*

On your laptop, open Jupyter or VS Code, start a **new** notebook in the folder that holds the downloaded file, and paste this in. It is text here, not a cell, so that you cannot run it on the cloud machine by accident.

```python
# RUNS ON: laptop
import socket
import pandas as pd
import matplotlib.pyplot as plt

print("This code is running on:", socket.gethostname())

small = pd.read_csv("ca_tmax_2024_daily.csv", parse_dates=["date"])

fig, ax = plt.subplots(figsize=(9, 4))
ax.fill_between(small["date"], small["coolest"], small["hottest"], alpha=0.2,
                label="coolest to hottest station")
ax.plot(small["date"], small["average"], label="average of all stations")
ax.set_title("Daily high temperature across California stations, 2024")
ax.set_ylabel("°C")
ax.legend()
fig.savefig("ca_tmax_2024.png", dpi=150, bbox_inches="tight")
```

The computer name it prints should be your own, not the one from step 2. If `pandas` or `matplotlib` is missing, run `pip install pandas matplotlib` first.

### Step 5. Save your work and stop the cloud machine

*Code runs: nowhere. Data is stored: this notebook and the CSV on the SageMaker disk; the CSV, the chart, and your local notebook on your laptop.*

1. **Laptop:** save your local notebook. Keep `ca_tmax_2024.png`; you submit it with this notebook.
2. **SageMaker:** File → **Save Notebook**. Right-click this notebook in the file browser and **Download** a copy.
3. **Stop the instance.** If you are going straight on to Part 2, leave it running and stop it at Q13, which uses these same steps. Otherwise go to the Studio tab, open **JupyterLab**, click **Stop** on `gsb5544`, and wait for *Stopped*.

A stopped space keeps its disk, so your files are there next time. Its RAM is wiped, so `raw` and `summary` are gone and that is fine. You created nothing in S3, so there is nothing to delete there.

### Two questions

**P1. What happened in the cloud?** In two or three sentences, name which service *stored* the 4.4 million rows and which one *processed* them, and say why you did not have to pay to store them.

*Your answer:*

**P2. What happened on your own computer?** In two or three sentences, say what your laptop stored and processed, how large the file was that travelled between the two machines, and why that made the laptop step easy.

*Your answer:*

---

## Part 2 · The inventory questions
"""),

md("""
**Athena setup** (given; it is block J of the topics-of-practice notebook, unchanged). It creates your results bucket if needed, defines the helpers, and defines the `gsb5544.ghcn` table over the public Parquet files. DDL is free.
"""),

code("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
sts     = boto3.client("sts",    region_name=REGION)
athena  = boto3.client("athena", region_name=REGION)
s3_mine = boto3.client("s3",     region_name=REGION)

ACCOUNT        = sts.get_caller_identity()["Account"]
RESULTS_BUCKET = f"gsb5544-athena-{ACCOUNT}"
RESULTS        = f"s3://{RESULTS_BUCKET}/athena/"
s3_mine.create_bucket(Bucket=RESULTS_BUCKET)

ATHENA_BYTES = 0                                  # running total of everything scanned today; Q13 audits it

def run_athena(sql, database=None):
    \"\"\"Start a query, wait for it, return (query id, statistics).\"\"\"
    global ATHENA_BYTES
    kwargs = {"QueryString": sql, "ResultConfiguration": {"OutputLocation": RESULTS}}
    if database:
        kwargs["QueryExecutionContext"] = {"Database": database}
    qid = athena.start_query_execution(**kwargs)["QueryExecutionId"]
    while True:
        q = athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]
        state = q["Status"]["State"]
        if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(1)
    if state != "SUCCEEDED":
        raise RuntimeError(q["Status"].get("StateChangeReason", state))
    ATHENA_BYTES += q["Statistics"].get("DataScannedInBytes", 0)
    return qid, q["Statistics"]


def athena_df(qid):
    \"\"\"Read a finished query's result CSV from the results bucket.\"\"\"
    obj = s3_mine.get_object(Bucket=RESULTS_BUCKET, Key=f"athena/{qid}.csv")
    return pd.read_csv(io.BytesIO(obj["Body"].read()))


run_athena("CREATE DATABASE IF NOT EXISTS gsb5544")
run_athena('''
CREATE EXTERNAL TABLE IF NOT EXISTS gsb5544.ghcn (
    id string, `date` string, data_value bigint,
    m_flag string, q_flag string, s_flag string, obs_time string
)
PARTITIONED BY (year int, element string)
STORED AS PARQUET
LOCATION 's3://noaa-ghcn-pds/parquet/by_year/'
TBLPROPERTIES (
    'projection.enabled'        = 'true',
    'projection.year.type'      = 'integer',
    'projection.year.range'     = '1750,2030',
    'projection.element.type'   = 'enum',
    'projection.element.values' = 'TMAX,TMIN,PRCP,SNOW,SNWD,TAVG',
    'storage.location.template' = 's3://noaa-ghcn-pds/parquet/by_year/YEAR=${year}/ELEMENT=${element}/'
)
''', database="gsb5544")
print("Ready. Results bucket:", RESULTS_BUCKET)
"""),

# ---------------------------------------------------------------- Set 1
md("""
## Set 1 · Capacity

### Q1. Two machines
Report physical cores, total RAM, available RAM, and free disk in GB for **this** machine (the SageMaker instance) and for **your laptop** (the numbers you wrote down from the reading, §1), as one DataFrame with a row per measure and a column per machine. Store this machine's available RAM in bytes as `MY_RAM`.

Then, in the markdown cell, one sentence: which machine would you rather use to read a 1.3 GB file from `noaa-ghcn-pds`, and why?
"""),
answer("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
vm = psutil.virtual_memory()
du = psutil.disk_usage("/")
MY_RAM = vm.available

machines = pd.DataFrame({
    "laptop": {                      # from the reading, §1
        "physical cores":     0,
        "total RAM (GB)":     0.0,
        "available RAM (GB)": 0.0,
        "free disk (GB)":     0.0,
    },
    "SageMaker ml.t3.medium": {
        "physical cores":     psutil.cpu_count(logical=False),
        "total RAM (GB)":     round(vm.total / 1e9, 1),
        "available RAM (GB)": round(vm.available / 1e9, 1),
        "free disk (GB)":     round(du.free / 1e9, 1),
    },
})
machines
"""),
md("""
*Your answer:*

"""),

md("""
### Q2. Rows that fit
A GHCN row is roughly 50 bytes on disk, and a text-heavy CSV needs about 3× its disk size once loaded in pandas. How many raw rows could this machine's available RAM hold? Print the number with thousands separators.
"""),
answer("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
BYTES_PER_ROW = 50
MULT = 3
rows_fit = MY_RAM // (BYTES_PER_ROW * MULT)
print(f"About {rows_fit:,} rows fit in {human(MY_RAM)} of available RAM on this instance")
"""),

md("""
### Q3. A decade of weather
List the by-year files for 2016 through 2025 and compute their **total** size. Print the total in readable units, then print how many copies of this machine's available RAM that is.

*Hint: a `Prefix` of `csv/by_year/201` returns 2010–2019; you will need two listings or a filter.*
"""),
answer("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
total = 0
for prefix in ["csv/by_year/201", "csv/by_year/202"]:
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
    for obj in resp["Contents"]:
        year = int(obj["Key"].split("/")[-1][:4])
        if 2016 <= year <= 2025:
            total += obj["Size"]
            print(f"{obj['Key']:<28} {human(obj['Size'])}")

print()
print("Total 2016–2025 :", human(total))
print("Copies of my RAM:", f"{total / MY_RAM:.1f}×")
"""),

# ---------------------------------------------------------------- Set 2
md("""
## Set 2 · Vocabulary in action

### Q4. What is under `csv/`?
List the common prefixes directly under `csv/` in the bucket. Then, in the markdown cell that follows, explain in one or two sentences why `by_year/` is not a folder and what S3 is actually doing when it shows you one.
"""),
answer("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
resp = s3.list_objects_v2(Bucket=BUCKET, Prefix="csv/", Delimiter="/")
print([p["Prefix"] for p in resp.get("CommonPrefixes", [])])
"""),
md("""
*Your answer:*

"""),

md("""
### Q5. Metadata only
Using a single call that does **not** download the file, print the size (readable) and the last-modified date of `csv/by_year/2024.csv`. Then print whether a plain `pd.read_csv` of it would fit in this machine's RAM at 3×.
"""),
answer("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
meta = s3.head_object(Bucket=BUCKET, Key="csv/by_year/2024.csv")
size = meta["ContentLength"]
print("Size         :", human(size))
print("Last modified:", meta["LastModified"])
print("Fits at 3×?  :", size * 3 < MY_RAM)
"""),

# ---------------------------------------------------------------- Set 3
md("""
## Set 3 · Extraction

### Q6. Pull both markets
Write a function `load_station(station_id)` that:

1. prints the object's size before reading it,
2. checks whether the file has a header row using a range request,
3. reads the file keeping only `id`, `date`, `element`, `value`,
4. converts `date` to a datetime,
5. keeps only `TMAX` and `PRCP` rows from **2015 onward**,
6. returns the DataFrame.

Call it for both stations and combine the results into one DataFrame called `wx` with a `market` column.

This runs on the SageMaker instance: the bytes travel from S3 to this machine over AWS's network in the same region, and never touch your laptop.
"""),
answer("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
def load_station(station_id):
    key = f"csv/by_station/{station_id}.csv"
    print(station_id, "size:", human(s3.head_object(Bucket=BUCKET, Key=key)["ContentLength"]))

    first = s3.get_object(Bucket=BUCKET, Key=key, Range="bytes=0-99")["Body"].read().decode()
    has_header = first.upper().startswith("ID,")

    raw = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
    df = pd.read_csv(
        io.BytesIO(raw),
        header=0 if has_header else None,
        names=COLS,
        usecols=["id", "date", "element", "value"],
        dtype={"id": "string", "element": "string"},
    )
    df["date"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d")
    df = df[df["element"].isin(["TMAX", "PRCP"]) & (df["date"] >= "2015-01-01")]
    return df.reset_index(drop=True)


frames = []
for market, sid in STATIONS.items():
    d = load_station(sid)
    d["market"] = market
    frames.append(d)

wx = pd.concat(frames, ignore_index=True)
print(wx.shape)
wx.groupby(["market", "element"]).size()
"""),

md("""
### Q7. Hot days per year
Temperatures are stored in tenths of a degree Celsius. For each market and year, count the number of days with a daily maximum of **35 °C or higher** (95 °F). Produce a table with years as rows and markets as columns.
"""),
answer("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
tmax = wx[wx["element"] == "TMAX"].copy()
tmax["tmax_c"] = tmax["value"] / 10
tmax["year"] = tmax["date"].dt.year

hot = (
    tmax[tmax["tmax_c"] >= 35]
    .groupby(["year", "market"]).size()
    .unstack("market")
    .fillna(0).astype(int)
)
hot
"""),

md("""
### Q8. Monthly rainfall
Precipitation is stored in tenths of a millimeter. For each market, compute total precipitation per month in millimeters, then show the **average for each calendar month** across all years (so 12 rows per market). Which month is wettest in each market?
"""),
answer("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
prcp = wx[wx["element"] == "PRCP"].copy()
prcp["prcp_mm"] = prcp["value"] / 10

monthly_total = (
    prcp.set_index("date")
        .groupby("market")["prcp_mm"]
        .resample("ME").sum()           # "M" on pandas < 2.2
        .reset_index()
)
monthly_total["month"] = monthly_total["date"].dt.month

climatology = monthly_total.groupby(["market", "month"])["prcp_mm"].mean().unstack("market").round(1)
print(climatology)
print()
print("Wettest month:", climatology.idxmax().to_dict())
"""),

# ---------------------------------------------------------------- Set 4
md("""
## Set 4 · Visualize and interpret

### Q9. One chart, two markets
Plot hot days per year (from Q7) for both markets on a single line chart. Label the axes with units and give the chart a title that says what it shows.
"""),
answer("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
fig, ax = plt.subplots(figsize=(9, 4))
for market in hot.columns:
    ax.plot(hot.index, hot[market], marker="o", linewidth=1.3, label=market)
ax.set_xlabel("Year")
ax.set_ylabel("Days with max temperature ≥ 35 °C")
ax.set_title("Hot days per year, 2015 onward")
ax.grid(alpha=0.3)
ax.legend()
plt.tight_layout()
plt.show()
"""),

md("""
### Q10. The business read
In five to seven sentences, answer as the inventory planner:

- What does the chart imply about how differently the two markets should be stocked across the year?
- Name **two** other datasets you would want to join to this weather history before trusting a demand model, and say where each one probably lives (your laptop, a company database, or a cloud bucket).
- This weather history will be refreshed **every week** once the model is live. Of the three places this module's code can run (your laptop, a SageMaker instance, the Athena fleet), which would you choose for that weekly refresh, and why? Answer from the reading now; revise after Q11 if the numbers change your mind.

*Your answer:*

"""),

# ---------------------------------------------------------------- Set 5
md("""
## Set 5 · Where the work runs

### Q11. Three ways to get the same rows
Extract the **Phoenix `TMAX` and `PRCP` rows for 2024** three ways and time each one:

- **(a) Laptop.** You already did this before class: the timed chunked read of `csv/by_year/2024.csv` in the reading, §6. Paste your `LAPTOP_SECONDS` into the cell. (That read was for the San Luis Obispo station; same file, same amount of work.)
- **(b) SageMaker.** Run the same chunked read here, filtering each one-million-row chunk to the Phoenix station. Time it.
- **(c) Athena.** Query `gsb5544.ghcn` for the same rows. Time it and record the bytes scanned.

Build a DataFrame `race` with one row per tier and columns for seconds, bytes moved or scanned, and rows returned. Also confirm that (b) and (c) return the same row count as filtering `wx` to Phoenix and 2024.

In the markdown cell after, explain which tier you would use for this extraction and why, using the phrase "filter at the source." Say what changed between (a) and (b), and what changed between (b) and (c).
"""),
answer("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
LAPTOP_SECONDS = 0.0             # <- paste from the reading, §6

key = "csv/by_year/2024.csv"
by_year_bytes = s3.head_object(Bucket=BUCKET, Key=key)["ContentLength"]
first = s3.get_object(Bucket=BUCKET, Key=key, Range="bytes=0-99")["Body"].read().decode()
has_header = first.upper().startswith("ID,")

t0 = time.perf_counter()
chunks = pd.read_csv(
    f"s3://{BUCKET}/{key}",
    storage_options={"anon": True},
    header=0 if has_header else None,
    names=COLS,
    usecols=["id", "date", "element", "value"],
    dtype={"id": "string", "element": "string"},
    chunksize=1_000_000,
)
sm_rows = pd.concat(c[c["id"] == STATIONS["Phoenix"]] for c in chunks)
sm_rows = sm_rows[sm_rows["element"].isin(["TMAX", "PRCP"])]
SAGEMAKER_SECONDS = time.perf_counter() - t0
print(f"SageMaker: {len(sm_rows):,} rows in {SAGEMAKER_SECONDS:,.0f} s, read {human(by_year_bytes)}")
"""),
answer("""
# RUNS ON: Athena fleet (results land in S3)
SQL = f'''
SELECT id, "date", data_value
FROM   gsb5544.ghcn
WHERE  year = 2024
  AND  element IN ('TMAX', 'PRCP')
  AND  id = '{STATIONS["Phoenix"]}'
'''

t0 = time.perf_counter()
qid, stats = run_athena(SQL, database="gsb5544")
athena_rows = athena_df(qid)
ATHENA_SECONDS = time.perf_counter() - t0
athena_bytes = stats["DataScannedInBytes"]

by_station = wx[(wx["market"] == "Phoenix") & (wx["date"].dt.year == 2024)]

race = pd.DataFrame(
    {
        "seconds":                [LAPTOP_SECONDS, SAGEMAKER_SECONDS, ATHENA_SECONDS],
        "bytes moved or scanned": [by_year_bytes, by_year_bytes, athena_bytes],
        "rows returned":          [None, len(sm_rows), len(athena_rows)],
    },
    index=["laptop", "SageMaker ml.t3.medium", "Athena fleet"],
)
race["readable"] = race["bytes moved or scanned"].map(human)
race["seconds"] = race["seconds"].round(1)

print(f"by_station path from Q6: {len(by_station):,} rows (read {human(sum(s3.head_object(Bucket=BUCKET, Key=f'csv/by_station/{sid}.csv')['ContentLength'] for sid in STATIONS.values()))} for both markets, all years)")
race
"""),
md("""
*Your answer:*

"""),

md("""
### Q12. Hot days, straight from the fleet
Write **one Athena query** that returns the number of hot days (`TMAX` ≥ 35 °C, i.e. `data_value >= 350`) per station per year from 2015 onward, for both stations: the same table you built in Q7, but computed entirely on the fleet. Pivot the result to years as rows and markets as columns and check it against `hot`.

Then print two numbers side by side: the bytes Athena scanned for this query, and the bytes pandas read in Q6 (the two by-station CSVs).

In the markdown cell, explain the comparison. One of the two paths read fewer bytes. Which, and why? What does that tell you about when Athena over `by_year` is the right tool, and when choosing the right object (the by-station file) beats it?
"""),
answer("""
# RUNS ON: Athena fleet (results land in S3)
SQL = f'''
SELECT id, year, COUNT(*) AS hot_days
FROM   gsb5544.ghcn
WHERE  element = 'TMAX'
  AND  year >= 2015
  AND  id IN ('{STATIONS["San Luis Obispo"]}', '{STATIONS["Phoenix"]}')
  AND  data_value >= 350
GROUP BY id, year
ORDER BY year, id
'''

qid, stats = run_athena(SQL, database="gsb5544")
id_to_market = {v: k for k, v in STATIONS.items()}

hot_athena = (
    athena_df(qid)
    .assign(market=lambda d: d["id"].map(id_to_market))
    .pivot(index="year", columns="market", values="hot_days")
    .fillna(0).astype(int)
)

athena_bytes = stats["DataScannedInBytes"]
pandas_bytes = sum(
    s3.head_object(Bucket=BUCKET, Key=f"csv/by_station/{sid}.csv")["ContentLength"]
    for sid in STATIONS.values()
)

print(f"Athena scanned : {human(athena_bytes):>9}   about ${max(athena_bytes, 10_000_000) / 1e12 * 5:.4f}")
print(f"pandas read    : {human(pandas_bytes):>9}   (the two by-station CSVs in Q6)")
same = (hot_athena == hot.reindex(hot_athena.index)[hot_athena.columns]).all().all()
print("Matches Q7     :", bool(same))
hot_athena
"""),
md("""
*Your answer:*

"""),

md("""
### Q13. Cost audit and teardown (graded)
Every session on a rented machine ends the same way. Four parts; the last one is the evidence.

**(a) Empty the results bucket.** Print the number of objects and their total size before deleting, then confirm the bucket is empty.

**(b) Estimate today's spend.** Hours this space has been running × the `ml.t3.medium` hourly price, plus `ATHENA_BYTES` × the Athena price per TB (10 MB minimum per query). Print the two lines and the total. The cell reads the space's start time from SageMaker; if that lookup fails, set `hours` by hand from the time you clicked **Run space** (Learner Lab: from the lab timer).

**(c) Stop the space.** In Studio → JupyterLab spaces, click **Stop** on `gsb5544` and wait for *Stopped*. Then read **Credits remaining** on Console Home (Learner Lab: the budget on the lab page).

**(d) Evidence.** Either paste a screenshot into the markdown cell showing the space *Stopped* and the credits readout, or run the verification cell from your **laptop** (it needs AWS credentials in `~/.aws/credentials`; Learner Lab users paste the "AWS Details" block there first) and paste its output into the markdown cell.
"""),
answer("""
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
# (a) empty the results bucket
listing = s3_mine.list_objects_v2(Bucket=RESULTS_BUCKET)
objects = listing.get("Contents", [])
print(f"Results bucket : {len(objects)} objects, {human(sum(o['Size'] for o in objects))}")
if objects:
    s3_mine.delete_objects(Bucket=RESULTS_BUCKET, Delete={"Objects": [{"Key": o["Key"]} for o in objects]})
print("Bucket empty   :", "Contents" not in s3_mine.list_objects_v2(Bucket=RESULTS_BUCKET))

# (b) today's spend
INSTANCE_PER_HOUR = 0.05         # ml.t3.medium, us-east-1, approximate
ATHENA_PER_TB     = 5.00

try:
    meta = json.load(open("/opt/ml/metadata/resource-metadata.json"))
    sm = boto3.client("sagemaker", region_name=REGION)
    app = sm.describe_app(DomainId=meta["DomainId"], SpaceName=meta["SpaceName"],
                          AppType=meta["AppType"], AppName=meta["ResourceName"])
    hours = (dt.datetime.now(dt.timezone.utc) - app["CreationTime"]).total_seconds() / 3600
except Exception as e:
    print("Could not read the space's start time:", e)
    hours = 3.0                  # <- set by hand: hours since you clicked Run space

instance_cost = hours * INSTANCE_PER_HOUR
athena_cost   = max(ATHENA_BYTES, 10_000_000) / 1e12 * ATHENA_PER_TB
print(f"Instance       : {hours:.2f} h × ${INSTANCE_PER_HOUR}/h = ${instance_cost:.3f}")
print(f"Athena         : {human(ATHENA_BYTES)} scanned  = ${athena_cost:.4f}")
print(f"Total today    : ${instance_cost + athena_cost:.3f}")
"""),

md("""
**Verification cell** for part (d). This one runs on your laptop *after* you have stopped the space, because a cell cannot stop the machine it is running on and then report on it.
"""),
code("""
# RUNS ON: laptop
# Needs AWS credentials in ~/.aws/credentials (Learner Lab: paste the "AWS Details" block there first).
import boto3

sm = boto3.client("sagemaker", region_name="us-east-1")
apps = sm.list_apps()["Apps"]
for a in apps:
    print(f'{a["AppType"]:<12} {a.get("SpaceName", ""):<12} {a["Status"]}')

still_running = [a for a in apps if a["Status"] not in ("Deleted", "Failed")]
print("All stopped" if not still_running else "STILL RUNNING: go back to Studio and stop it")
"""),
md("""
*Evidence (screenshot or pasted output):*

"""),

md("""
---

**Submit** this notebook with all cells run inside SageMaker, plus your Q13 evidence. Your written answers for Q1, Q4, Q10, Q11, and Q12 go in the markdown cells provided. A submission is not complete while its JupyterLab space is still running; we check.
"""),
]

# ======================================================================
build(nb2, "02_topics_of_practice.ipynb", student=True)
build(nb2, "02_topics_of_practice_SOLUTIONS.ipynb", student=False)
build(nb3, "03_practice_activity.ipynb", student=True)
build(nb3, "03_practice_activity_SOLUTIONS.ipynb", student=False)
print("built 4 notebooks")
