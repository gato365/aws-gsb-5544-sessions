"""
Builds four notebooks from one source of truth:
  02_topics_of_practice.ipynb            (fill-in-the-blank: ⟦...⟧ -> ____)
  02_topics_of_practice_SOLUTIONS.ipynb
  03_practice_activity.ipynb             (answer cells emptied)
  03_practice_activity_SOLUTIONS.ipynb
"""
import re
import nbformat as nbf

BLANK = "____"


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
            out.append(nbf.v4.new_code_cell("# your code here\n" if student else src))
    nb.cells = out
    nbf.write(nb, path)
    # sanity: every code cell in the solutions version must compile
    if not student:
        for c in nb.cells:
            if c.cell_type == "code":
                compile(c.source, path, "exec")


# ======================================================================
# NOTEBOOK 2 — Topics of practice (fill in the blanks)
# ======================================================================
nb2 = [
md("""
# Topics of Practice: Data Bigger Than Your Laptop

**GSB 5544 · Computing and Machine Learning for Business Analytics**

This notebook walks through the main functions from the pre-class reading, one short block at a time. Each block names the section of the reading it draws on. Replace every `____` with the right code and run the cell.

You need: `psutil`, `boto3`, `s3fs`, `pandas`, `matplotlib`. No AWS account is required.
"""),

code("""
import io
import psutil
import boto3
import pandas as pd
import matplotlib.pyplot as plt
from botocore import UNSIGNED
from botocore.config import Config

BUCKET = "noaa-ghcn-pds"
"""),

# ---------------------------------------------------------------- A
md("""
## A. What your machine actually has

*From the reading, §1.* Total RAM is not available RAM. The available number decides whether a file loads.

Fill in the two calls that report memory and the attribute that gives the memory available **right now**.
"""),

code("""
vm = psutil.⟦virtual_memory⟧()
du = psutil.disk_usage("/")

print(f"Physical cores : {psutil.cpu_count(logical=False)}")
print(f"Total RAM      : {vm.total / 1e9:.1f} GB")
print(f"Available RAM  : {vm.⟦available⟧ / 1e9:.1f} GB")
print(f"Free disk      : {du.free / 1e9:.1f} GB")

MY_RAM = vm.⟦available⟧          # keep this; we compare file sizes against it below
"""),

# ---------------------------------------------------------------- B
md("""
## B. The units of data

*From the reading, §2.* Byte counts are unreadable past a few million. Write the helper that turns them into KB / MB / GB and so on, using base 1000.

Fill in the list of units in ascending order and the line that steps `n` down one unit.
"""),

code("""
def human(n, base=1000):
    for unit in [⟦"B", "KB", "MB", "GB", "TB", "PB"⟧]:
        if n < base:
            return f"{n:,.1f} {unit}"
        n ⟦/= base⟧
    return f"{n:,.1f} EB"

print(human(1_500_000))          # expect 1.5 MB
print(human(1_336_457_184))      # expect 1.3 GB
print(human(MY_RAM))             # your available RAM, readable
"""),

md("""
**Check yourself.** A "1 TB" drive shows as 931 GB in your file browser. Which base does the drive maker use, and which does the operating system use? Write your answer in the cell below as a comment.
"""),

code("""
# Drive maker uses base ⟦1000⟧; the OS uses base ⟦1024⟧.
# 1e12 / 1024**3 = ⟦931.3⟧ GiB, which the OS labels "GB".
"""),

# ---------------------------------------------------------------- C
md("""
## C. The vocabulary of AWS

*From the reading, §3.* Fill in the term that each definition describes. The cell checks your answers.
"""),

code("""
vocab = {
    "A named container for objects; its name is globally unique":     "⟦bucket⟧",
    "One stored item plus its metadata such as size":                  "⟦object⟧",
    "The full name of an object inside its bucket":                    "⟦key⟧",
    "The start of a key, used to list everything 'under' something":   "⟦prefix⟧",
    "A geographic cluster of data centers such as us-east-1":          "⟦region⟧",
    "A rented virtual computer":                                       "⟦EC2⟧",
    "The service that decides who may do what":                        "⟦IAM⟧",
}

expected = {"bucket", "object", "key", "prefix", "region", "ec2", "iam"}
given = {v.strip().lower() for v in vocab.values()}
print("All correct" if given == expected else f"Check: {expected - given}")
"""),

# ---------------------------------------------------------------- D
md("""
## D. Connect without an account

*From the reading, §4.* Public datasets on S3 can be read with an **unsigned** request. Build the client, then list the top-level "folders" of the GHCN bucket.

Fill in the signature setting that makes the request anonymous, and the delimiter that makes S3 group keys like folders.
"""),

code("""
s3 = boto3.client(
    "s3",
    region_name="us-east-1",
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
# ⟦It is a prefix: the shared beginning of many object keys. S3 groups keys by it when asked, which looks like a folder.⟧
"""),

# ---------------------------------------------------------------- E
md("""
## E. Read a size without reading the file

*From the reading, §4.* Every object carries its size as metadata. List the by-year files for the 2020s and print each size in readable units.

Fill in the prefix that selects `csv/by_year/2020.csv` through `2026.csv`, and the field that holds an object's size.
"""),

code("""
resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=⟦"csv/by_year/202"⟧)

sizes = {}
for obj in resp["Contents"]:
    sizes[obj["Key"]] = obj[⟦"Size"⟧]
    print(f"{obj['Key']:<28} {human(obj[⟦'Size'⟧])}")
"""),

md("""
Now the comparison that the whole reading builds toward. pandas typically needs about **3×** a text CSV's size in memory. For each file, decide whether a plain `pd.read_csv` would fit in your available RAM.

Fill in the multiplier and the comparison.
"""),

code("""
MULT = ⟦3⟧

for key, size in sizes.items():
    need = size * MULT
    fits = need ⟦<⟧ MY_RAM
    print(f"{key:<28} needs ~{human(need):>9}   fits: {fits}")
"""),

# ---------------------------------------------------------------- F
md("""
## F. Peek at a file with a range request

*From the reading, §4.* You can read the first few hundred bytes of a gigabyte file to see its shape. Do that for the 2024 by-year file and check whether it has a header row.

Fill in the `Range` header for the first 300 bytes.
"""),

code("""
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

*From the reading, §5.* Lever 1 is picking the right object. The Cal Poly station (`USC00047851`, SAN LUIS OBISPO POLY) has records since 1893 in a single file of about 7 MB. Read it, keeping only the four columns you need.

Fill in the station key, the header logic, and the `usecols` list.
"""),

code("""
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

*From the reading, §5, "The units trap".* Dates are stored as `YYYYMMDD` integers and temperatures in tenths of a degree Celsius. Fix both, keep only daily maximum temperature, and compute a yearly mean.

Fill in the date format string, the element code, the unit conversion, and the resampling rule for year-end.
"""),

code("""
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

*From the reading, §6.* One picture that came from a bucket you never downloaded.

Fill in the series to plot and the y-axis label with its unit.
"""),

code("""
fig, ax = plt.subplots(figsize=(9, 4))
ax.plot(yearly.index, ⟦yearly.values⟧, linewidth=1.2)
ax.set_ylabel(⟦"Mean daily maximum (°C)"⟧)
ax.set_title(f"{STATION}: yearly mean of daily maximum temperature")
ax.grid(alpha=0.3)
plt.tight_layout()
plt.show()
"""),

md("""
## Before you leave

Write one sentence, as a comment, that answers: *why did reading the station file work when reading the year file would not have?*
"""),

code("""
# ⟦The station file holds only the rows I needed, about 7 MB. The year file holds every station on Earth, 1.3 GB, and I would have thrown almost all of it away. Choosing the object was the filter.⟧
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

Everything you need is in the pre-class reading. Each question has an empty code cell; some also ask for a short written answer in a markdown cell.

**Stations**

| Market | Station ID | Name |
|---|---|---|
| San Luis Obispo | `USC00047851` | SAN LUIS OBISPO POLY, CA |
| Phoenix | `USW00023183` | PHOENIX AIRPORT, AZ |

Run the setup cell first.
"""),

code("""
import io
import time
import psutil
import boto3
import pandas as pd
import matplotlib.pyplot as plt
from botocore import UNSIGNED
from botocore.config import Config

BUCKET = "noaa-ghcn-pds"
COLS = ["id", "date", "element", "value", "m_flag", "q_flag", "s_flag", "obs_time"]
STATIONS = {"San Luis Obispo": "USC00047851", "Phoenix": "USW00023183"}

s3 = boto3.client("s3", region_name="us-east-1", config=Config(signature_version=UNSIGNED))


def human(n, base=1000):
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if n < base:
            return f"{n:,.1f} {unit}"
        n /= base
    return f"{n:,.1f} EB"
"""),

# ---------------------------------------------------------------- Set 1
md("""
## Set 1 · Capacity

### Q1. Your machine
Report physical cores, total RAM, available RAM, and free disk in GB. Store available RAM in bytes as `MY_RAM`.
"""),
answer("""
vm = psutil.virtual_memory()
du = psutil.disk_usage("/")
MY_RAM = vm.available

print(f"Physical cores : {psutil.cpu_count(logical=False)}")
print(f"Total RAM      : {vm.total / 1e9:.1f} GB")
print(f"Available RAM  : {vm.available / 1e9:.1f} GB")
print(f"Free disk      : {du.free / 1e9:.1f} GB")
"""),

md("""
### Q2. Rows that fit
A GHCN row is roughly 50 bytes on disk, and a text-heavy CSV needs about 3× its disk size once loaded in pandas. How many raw rows could your available RAM hold? Print the number with thousands separators.
"""),
answer("""
BYTES_PER_ROW = 50
MULT = 3
rows_fit = MY_RAM // (BYTES_PER_ROW * MULT)
print(f"About {rows_fit:,} rows fit in {human(MY_RAM)} of available RAM")
"""),

md("""
### Q3. A decade of weather
List the by-year files for 2016 through 2025 and compute their **total** size. Print the total in readable units, then print how many copies of your available RAM that is.

*Hint: a `Prefix` of `csv/by_year/201` returns 2010–2019; you will need two listings or a filter.*
"""),
answer("""
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
resp = s3.list_objects_v2(Bucket=BUCKET, Prefix="csv/", Delimiter="/")
print([p["Prefix"] for p in resp.get("CommonPrefixes", [])])
"""),
md("""
*Your answer:*

"""),

md("""
### Q5. Metadata only
Using a single call that does **not** download the file, print the size (readable) and the last-modified date of `csv/by_year/2024.csv`. Then print whether a plain `pd.read_csv` of it would fit in your RAM at 3×.
"""),
answer("""
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
"""),
answer("""
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
In four to six sentences, answer as the inventory planner:

- What does the chart imply about how differently the two markets should be stocked across the year?
- Name **two** other datasets you would want to join to this weather history before trusting a demand model, and say where each one probably lives (your laptop, a company database, or a cloud bucket).

*Your answer:*

"""),

md("""
### Q11. Stretch: the wrong way, on purpose
Extract the **same Phoenix rows for 2024** by reading `csv/by_year/2024.csv` in chunks of one million rows, filtering each chunk to the Phoenix station. Time it. Then compare the row count to what you get by filtering `wx` to Phoenix and 2024.

In the markdown cell after, explain which extraction is better and why, using the phrase "filter at the source."

*This reads 1.3 GB over the network. Expect several minutes. Skip if your connection is slow.*
"""),
answer("""
key = "csv/by_year/2024.csv"
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
by_year = pd.concat(c[c["id"] == STATIONS["Phoenix"]] for c in chunks)
by_year = by_year[by_year["element"].isin(["TMAX", "PRCP"])]
elapsed = time.perf_counter() - t0

by_station = wx[(wx["market"] == "Phoenix") & (wx["date"].dt.year == 2024)]

print(f"by_year   : {len(by_year):,} rows in {elapsed:,.0f} s (read {human(s3.head_object(Bucket=BUCKET, Key=key)['ContentLength'])})")
print(f"by_station: {len(by_station):,} rows (read {human(s3.head_object(Bucket=BUCKET, Key='csv/by_station/USW00023183.csv')['ContentLength'])})")
"""),
md("""
*Your answer:*

"""),

md("""
---

**Submit** this notebook with all cells run. Your written answers for Q4, Q10, and Q11 go in the markdown cells provided.
"""),
]

# ======================================================================
build(nb2, "02_topics_of_practice.ipynb", student=True)
build(nb2, "02_topics_of_practice_SOLUTIONS.ipynb", student=False)
build(nb3, "03_practice_activity.ipynb", student=True)
build(nb3, "03_practice_activity_SOLUTIONS.ipynb", student=False)
print("built 4 notebooks")
