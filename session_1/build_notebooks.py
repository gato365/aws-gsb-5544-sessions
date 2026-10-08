"""
Builds every Session 1 notebook from one source of truth.

  02_topics_of_practice                 remote   (fill-in-the-blank)
  03_practice_activity_remote           remote   (guided workflow, steps 1-6, and the remote half of the timing test)
  03_practice_activity_local            local    (steps 7-8, and the local half of the timing test)
  04_lab_remote                         remote   (inventory-planning lab: analyze and export)
  04_lab_local                          local    (inventory-planning lab: visualize and interpret)
  05_athena_extension                   remote   (optional; not part of the required session)

Each is written twice: the student version and a _SOLUTIONS version, both into this folder.
  A copy of each _SOLUTIONS notebook is also placed in the instructor's course folder (INSTRUCTOR_COPY).

Conventions
  ⟦...⟧     text that becomes a blank (____) in the student version
  answer()  a code cell that is emptied in the student version; its
            "# RUNS ON:" first line is kept so students still see where it is meant to run
  Every code cell's source begins with one of exactly three lines:
      # RUNS ON: laptop (Positron)
      # RUNS ON: SageMaker (remote)
      # RUNS ON: Athena (AWS-managed)
  The comment names the INTENDED environment. It does not move execution anywhere:
  a cell runs on whichever computer's kernel the notebook is attached to. That is why
  every notebook also calls where_am_i(), which checks the machine it is really on.

  build() refuses to write a notebook where a code cell lacks a RUNS ON line or carries
  one that does not belong in that notebook, and compiles every solution cell
  (IPython %/! lines are stripped before compiling).

Run:  python build_notebooks.py        (needs nbformat)
"""
import re
import nbformat as nbf

BLANK = "____"
LOCAL = "# RUNS ON: laptop (Positron)"
REMOTE = "# RUNS ON: SageMaker (remote)"
ATHENA = "# RUNS ON: Athena (AWS-managed)"


def md(src):
    return ("md", src.strip("\n"))


def code(src):
    return ("code", src.strip("\n"))


def answer(src):
    """A code cell that is fully hidden in the student version."""
    return ("answer", src.strip("\n"))


def build(cells, path, student, allowed):
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

    # sanity 1: every code cell says where it is meant to run, and the label belongs in this notebook
    for c in nb.cells:
        if c.cell_type == "code":
            first = c.source.splitlines()[0] if c.source else ""
            if first not in allowed:
                raise SystemExit(f"{path}: code cell with a missing or misplaced RUNS ON line:\n{c.source[:120]}")

    # sanity 2: every code cell in the solutions version must compile
    if not student:
        for c in nb.cells:
            if c.cell_type == "code":
                plain = "\n".join(l for l in c.source.splitlines() if not l.lstrip().startswith(("%", "!")))
                compile(plain, path, "exec")

    nbf.write(nb, path)


# ======================================================================
# Shared, supplied code. Students do not rebuild this boilerplate.
# ======================================================================
HELPERS = '''
def human(n, base=1000):
    """Turn a byte count into a readable string. base=1000 gives KB/MB/GB; base=1024 gives KiB/MiB/GiB."""
    units = ["B", "KB", "MB", "GB", "TB", "PB"] if base == 1000 else ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    for unit in units:
        if n < base:
            return f"{n:,.1f} {unit}"
        n /= base
    return f"{n:,.1f} (huge)"


def where_am_i():
    """Report which computer this kernel is really on. A RUNS ON comment cannot do that."""
    on_sagemaker = (os.path.exists("/opt/ml/metadata/resource-metadata.json")
                    or os.path.expanduser("~") == "/home/sagemaker-user")
    place = "SageMaker (remote)" if on_sagemaker else "not SageMaker (probably your laptop)"
    print("Computer name   :", socket.gethostname())
    print("This looks like :", place)
    return place


def machine_report(work_dir="."):
    """Measure the computer running this cell. Disk numbers are for the filesystem that holds work_dir."""
    vm = psutil.virtual_memory()
    du = psutil.disk_usage(work_dir)
    return {
        "computer name":                    socket.gethostname(),
        "physical CPU cores":               psutil.cpu_count(logical=False),   # may be None on some virtual machines
        "logical CPUs (vCPUs in the cloud)": psutil.cpu_count(logical=True),
        "total RAM (GB)":                   round(vm.total / 1e9, 1),
        "available RAM right now (GB)":     round(vm.available / 1e9, 1),
        "work disk, total (GB)":            round(du.total / 1e9, 1),
        "work disk, free (GB)":             round(du.free / 1e9, 1),
    }
'''.strip("\n")

S3_HELPERS = '''
def slice_prefix(year, element):
    """The key prefix of one year-and-element slice of the Parquet copy of GHCN-Daily."""
    return f"parquet/by_year/YEAR={year}/ELEMENT={element}/"


def prefix_size(prefix):
    """Count the objects under a prefix and add up their sizes, without reading any of them."""
    objects, total = 0, 0
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            objects += 1
            total += obj["Size"]
    return objects, total
'''.strip("\n")

REMOTE_SETUP = f'''
{REMOTE}
%pip install -q s3fs pyarrow psutil      # harmless if already present

import os
import json
import time
import socket
import psutil
import boto3
import pandas as pd
from botocore import UNSIGNED
from botocore.config import Config

BUCKET = "noaa-ghcn-pds"         # NOAA's public bucket
REGION = "us-east-1"             # the region the bucket is in; your SageMaker space should be in it too

# unsigned = anonymous: this client attaches no credentials, because the bucket is public
s3 = boto3.client("s3", region_name=REGION, config=Config(signature_version=UNSIGNED))


{HELPERS}


{S3_HELPERS}


if where_am_i() != "SageMaker (remote)":
    print()
    print("NOTE: this notebook is written to run in your SageMaker space, and this kernel is somewhere else.")
    print("      The RUNS ON comments describe the plan. They do not move the code. Open this file in JupyterLab on SageMaker.")
'''.strip("\n")

LOCAL_SETUP = f'''
{LOCAL}
%pip install -q pandas pyarrow s3fs psutil matplotlib      # harmless if already present

import os
import json
import time
import socket
import psutil
import pandas as pd
import matplotlib.pyplot as plt

BUCKET = "noaa-ghcn-pds"


{HELPERS}


if where_am_i() == "SageMaker (remote)":
    print()
    print("NOTE: this notebook is written to run on your laptop, in Positron, and this kernel is on SageMaker.")
    print("      Download this file and open it in Positron instead.")
'''.strip("\n")

# The controlled timing job. This exact text goes into BOTH practice notebooks.
TIMING_JOB = '''
TIMING_YEAR = 2024
TIMING_COLUMNS = ["ID", "DATE", "DATA_VALUE", "Q_FLAG"]


def timing_job():
    """Read one slice from S3, then summarize it. Returns the summary and the two measured times."""
    t0 = time.perf_counter()
    raw = pd.read_parquet(
        f"s3://{BUCKET}/parquet/by_year/YEAR={TIMING_YEAR}/ELEMENT=TMAX/",
        columns=TIMING_COLUMNS,
        storage_options={"anon": True},
    )
    t1 = time.perf_counter()                                    # reading ends here

    keep = raw[raw["ID"].str.startswith("USC0004") & raw["Q_FLAG"].isna()]
    daily = pd.DataFrame({
        "date":   pd.to_datetime(keep["DATE"].astype(str), format="%Y%m%d"),
        "tmax_c": keep["DATA_VALUE"] / 10,
    })
    summary = (daily.groupby("date")["tmax_c"]
                    .agg(stations="count", mean_tmax_c="mean")
                    .round({"mean_tmax_c": 2})
                    .reset_index())
    t2 = time.perf_counter()                                    # processing ends here

    times = {
        "read seconds":    round(t1 - t0, 2),
        "process seconds": round(t2 - t1, 2),
        "rows read":       len(raw),
        "summary rows":    len(summary),
    }
    return summary, times
'''.strip("\n")

WORKFLOW_TABLE = """
| Step | What you do | Where you are | Which computer runs code | Where the data is |
|---|---|---|---|---|
| 1 | Sign in to your own AWS account | Browser, AWS website | none | S3 (NOAA's public bucket) |
| 2 | Open and start your SageMaker space | Browser, SageMaker Studio | none yet | S3 |
| 3 | Read NOAA data from S3 | **Remote notebook** (JupyterLab tab) | **SageMaker** | S3 → SageMaker's RAM |
| 4 | Filter, transform, aggregate | **Remote notebook** | **SageMaker** | SageMaker's RAM |
| 5 | Save a small summary CSV | **Remote notebook** | **SageMaker** | SageMaker's disk |
| 6 | Download the summary | Browser, JupyterLab file browser | none (a file copy) | SageMaker's disk → your laptop's disk |
| 7 | Open it and make the chart | **Local notebook** (Positron) | **your laptop** | laptop's disk → laptop's RAM |
| 8 | Save your work and stop the space | Positron, then browser | none | your laptop's disk; SageMaker's disk |
""".strip("\n")

FIVE_QUESTIONS = """
1. **Where is the original data stored?**
2. **Which computer performed the analysis?**
3. **What did I download?**
4. **Which computer created the visualization?**
5. **How did the two machines compare?**
""".strip("\n")

STOP_CHECKLIST = """
- [ ] **Remote notebook:** File → **Save Notebook**. Right-click it in the JupyterLab file browser and **Download** a copy.
- [ ] **Studio tab:** on the `gsb5544` space page click **Stop space**, confirm in the dialog, and wait until the status reads **Stopped**. Closing the browser tab does not stop it.
- [ ] **Console Home** (open [console.aws.amazon.com](https://console.aws.amazon.com) in a new tab): read **Credits remaining** and note it. The panel can lag by several hours.
- [ ] **Laptop:** save your local notebook in Positron (Cmd+S, or Ctrl+S on Windows).
""".strip("\n")


# ======================================================================
# 02 — Topics of practice (remote, short, fill in the blanks)
# ======================================================================
topics = [
md("""
# Topics of Practice: Remote Computing on Data You Do Not Download

**GSB 5544 · Computing and Machine Learning for Business Analytics**

This notebook is short on purpose. It practices the middle of the workflow, the part that happens on a computer that is not yours:

> measure the remote machine → look at how big the data is → read a manageable piece → summarize it → save a small file

**Run this notebook in JupyterLab inside your SageMaker space** (reading, section 5, parts D and E), not in Positron. Replace each `____` and run the cell with Shift+Enter. If a cell stops with `NameError: name '____' is not defined`, you ran it before filling in its blank; fill the blank and run it again.

Every code cell starts with a `# RUNS ON:` comment. **That comment is a label for you. It does not move the code anywhere.** A cell runs on whichever computer the notebook's kernel is on. The setup cell checks where that really is.

Bring the laptop numbers you recorded in the reading, section 1.
"""),

code(REMOTE_SETUP),

md("""
The setup cell supplied the routine pieces so you do not have to rebuild them: `human()` for readable sizes, `where_am_i()`, `machine_report()`, `slice_prefix()`, and `prefix_size()`. Read their docstrings above; you will call them below.

## Start here: what stores, what computes

| | What it is | Stores data? | Runs your code? | What you pay for |
|---|---|---|---|---|
| **Your laptop** | The computer in front of you | Yes, on its disk | Yes, with its own CPU and RAM | Nothing extra |
| **SageMaker space** | A computer you rent in an AWS data center, with its own CPU, RAM, and a small disk | A little: notebooks and small files | Yes, with *its* CPU and RAM, not yours | Each hour its status is *Running* |
| **S3 bucket** | Storage only. Files kept in AWS, readable from your laptop or from SageMaker | Yes | **No.** It can only hand over bytes | Each GB stored per month (NOAA's bucket is paid for by AWS's open-data program, not by you) |

**Storing is not processing.** Data in S3 does nothing until some computer reads it. The bytes travel to wherever the code runs, and what that code loads must fit in **that** computer's RAM.

**Disk is not RAM.** Disk keeps files when the machine is off. RAM is the working space of a running program. S3, the remote machine's disk, and the remote machine's RAM are three different places.

Fill in each blank with `laptop`, `SageMaker`, or `S3`.
"""),

code(f'''
{REMOTE}
where = {{
    "Stores the NOAA weather files we read today":             "⟦S3⟧",
    "Runs the cells of this notebook":                         "⟦SageMaker⟧",
    "Shows you this notebook in a browser tab":                "⟦laptop⟧",
    "Can store data but cannot run any code":                  "⟦S3⟧",
    "Bills by the hour while Running, even when you are idle":  "⟦SageMaker⟧",
    "Will run Positron and draw the final chart":              "⟦laptop⟧",
}}

expected = ["s3", "sagemaker", "laptop", "s3", "sagemaker", "laptop"]
given = [v.strip().lower() for v in where.values()]
wrong = [q for q, g, e in zip(where, given, expected) if g != e]
print("All correct" if not wrong else "Check these: " + "; ".join(wrong))
'''),

# ---------------------------------------------------------------- A
md("""
## A. Measure the remote machine and compare it with your laptop

*Reading, section 1.* `machine_report()` measures the computer running this cell. Its disk numbers describe the filesystem that holds this notebook, which on SageMaker is the space's own small disk, **not S3**.

- **Physical cores** are real processor cores. **Logical CPUs** count what the operating system can schedule on; with hyper-threading one physical core appears as two. A cloud **vCPU** is one logical CPU, so "2 vCPUs" does not mean two physical cores.
- **Total RAM** is what is installed. **Available RAM** is what a new program could use right now. Available is the smaller number and the one that matters.

Fill in the function call, then paste in your laptop's numbers from the reading.
"""),

code(f'''
{REMOTE}
remote = ⟦machine_report⟧()
remote
'''),

code(f'''
{REMOTE}
laptop = {{                                   # <- replace every value with what you recorded in the reading, section 1
    "computer name":                     "my laptop",
    "physical CPU cores":                0,
    "logical CPUs (vCPUs in the cloud)": 0,
    "total RAM (GB)":                    0.0,
    "available RAM right now (GB)":      0.0,
    "work disk, total (GB)":             0.0,
    "work disk, free (GB)":              0.0,
}}

compare = pd.DataFrame({{"laptop": laptop, "SageMaker (remote)": ⟦remote⟧}})
compare
'''),

md("""
**Save this machine's details as a markdown file.** The cell below writes the remote report as a small `.md` table next to this notebook. Download it with the rest of your files; it is the record of which machine did today's work, and the instructor's copy of it is the *Remote machine reference* page on the course site.
"""),

code(f'''
{REMOTE}
import datetime as dt

try:                                                         # the space's own description of itself, if available
    meta = json.load(open("/opt/ml/metadata/resource-metadata.json"))
    space_info = {{"space name": meta.get("SpaceName"), "domain id": meta.get("DomainId"),
                  "app type": meta.get("AppType"), "region (from ARN)": meta.get("ResourceArn", "::::")[9:].split(":")[2]}}
except Exception:
    space_info = {{"space name": "not reported by this image"}}

lines = [f"# Remote machine report", "",
         f"Measured on {{dt.date.today().isoformat()}} by `machine_report()` inside SageMaker.", "",
         "| Measure | Value |", "|---|---|"]
lines += [f"| {{k}} | {{v}} |" for k, v in {{**space_info, **remote}}.items()]
report_text = "\\n".join(lines) + "\\n"

with open("remote_machine_report.md", "w") as f:
    f.write(report_text)
print(report_text)
'''),

md("""
**Check yourself.** Do not assume the rented machine is bigger or faster. Look at your table. Which machine has more available RAM? More logical CPUs? Answer in one comment, using your own numbers.
"""),

code(f'''
{REMOTE}
# ⟦Example: my laptop has 16 GB total and 5.1 GB available with 8 logical CPUs; the remote machine has about 4 GB total with 2 vCPUs. The remote machine is smaller. What it offers is location (next to the data) and that it can be resized, not size.⟧
'''),

# ---------------------------------------------------------------- B
md("""
## B. Bucket, object, key, and why this read is anonymous

*Reading, sections 3 and 4.* A **bucket** is a named container. An **object** is one stored file plus its metadata. A **key** is the object's full name inside the bucket. A **prefix** is the beginning of a key, which is how S3 imitates folders.

The `s3` client in the setup cell is **unsigned**: it sends no credentials. NOAA's bucket is public, so it answers anyone. You still needed your own AWS account today, but for a different reason: the account is what lets you **rent this computer**. The data is free to read; the computing is yours to pay for.

Fill in the delimiter that makes S3 group keys like folders, and the metadata field that holds an object's size.
"""),

code(f'''
{REMOTE}
resp = s3.list_objects_v2(Bucket=BUCKET, Delimiter=⟦"/"⟧)
print("Top-level prefixes:", [p["Prefix"] for p in resp.get("CommonPrefixes", [])])

key = "csv/by_year/2024.csv"                          # one object: a whole year, every station, as text
meta = s3.head_object(Bucket=BUCKET, Key=key)         # metadata only; the file is not downloaded
print("Bucket:", BUCKET)
print("Key   :", key)
print("Size  :", human(meta[⟦"ContentLength"⟧]))
'''),

# ---------------------------------------------------------------- C
md("""
## C. Look at the size before you read

*Reading, section 2.* The same year exists in the bucket twice: as one large CSV object, and as Parquet files split by year and element. Today we read the Parquet slice for 2024 daily highs (`TMAX`).

Fill in the helper that builds the slice's prefix, and the base that gives binary units.
"""),

code(f'''
{REMOTE}
prefix = ⟦slice_prefix⟧(2024, "TMAX")
objects, SOURCE_BYTES = prefix_size(prefix)

print("Prefix          :", prefix)
print("Objects         :", objects)
print("Size, decimal   :", human(SOURCE_BYTES))               # 1 MB = 1,000,000 bytes
print("Size, binary    :", human(SOURCE_BYTES, base=⟦1024⟧))  # 1 MiB = 1,048,576 bytes
print("The CSV year was:", human(meta["ContentLength"]))
'''),

md("""
The two size lines describe the same bytes in two unit systems. Storage and cloud consoles mostly use decimal units; operating systems often use binary ones.

Source-file size is **not** how much RAM the data will need. Text CSVs often grow when loaded and compressed Parquet often grows much more. There is no multiplier you can trust in advance, so the honest method is: start with a slice you know is small, load it, and **measure**.
"""),

# ---------------------------------------------------------------- D
md("""
## D. Read a manageable dataset into the remote machine's RAM

The bytes now travel from S3 to this SageMaker machine. Nothing reaches your laptop except the text printed below.

Fill in the setting that makes the read anonymous, and the argument that makes pandas count text columns honestly.
"""),

code(f'''
{REMOTE}
t0 = time.perf_counter()
raw = pd.read_parquet(
    f"s3://{{BUCKET}}/{{prefix}}",
    columns=["ID", "DATE", "DATA_VALUE", "Q_FLAG"],       # only the columns we need
    storage_options={{"anon": ⟦True⟧}},
)
READ_SECONDS = time.perf_counter() - t0

ROWS_READ = len(raw)
DF_BYTES = int(raw.memory_usage(deep=⟦True⟧).sum())

print(f"Rows read          : {{ROWS_READ:,}} in {{READ_SECONDS:.1f}} s")
print(f"Source files in S3 : {{human(SOURCE_BYTES)}}")
print(f"DataFrame in RAM   : {{human(DF_BYTES)}}   ({{DF_BYTES / SOURCE_BYTES:.0f}} times the source size, measured, not predicted)")
raw.head(3)
'''),

# ---------------------------------------------------------------- E
md("""
## E. Filter, transform, and aggregate, on the remote machine

GHCN-Daily has three conventions you must handle:

- `DATE` is text like `20240131`.
- `DATA_VALUE` for `TMAX` is in **tenths of a degree Celsius**: `183` means 18.3 °C.
- `Q_FLAG` is empty when a value passed NOAA's quality checks and holds a letter when it **failed**. Failed values are dropped. A day with no valid value is *missing*; it is never zero.

Summarize one station, the Cal Poly station in San Luis Obispo (`USC00047851`), by month.

Fill in the quality filter, the unit conversion, and the grouping column.
"""),

code(f'''
{REMOTE}
STATION = "USC00047851"                        # SAN LUIS OBISPO POLY, CA

one = raw[(raw["ID"] == STATION) & raw["Q_FLAG"].⟦isna⟧()].copy()
one["date"]   = pd.to_datetime(one["DATE"].astype(str), format="%Y%m%d")
one["tmax_c"] = one["DATA_VALUE"] ⟦/ 10⟧
one["month"]  = one["date"].dt.month

summary = (one.groupby(⟦"month"⟧)["tmax_c"]
              .agg(days_reported="count", mean_tmax_c="mean", hottest_c="max")
              .round(1)
              .reset_index())

print(f"{{ROWS_READ:,}} rows read, {{len(one):,}} kept for this station, {{len(summary)}} rows in the summary")
summary
'''),

# ---------------------------------------------------------------- F
md("""
## F. Save a small summary on the remote disk, and compare four sizes

The summary is written to **this machine's disk**, next to this notebook. It is not in S3 and not on your laptop yet. In the practice activity you will download a file like this and chart it in Positron; there is no chart here because the charting belongs on your laptop.

Fill in the method that writes a CSV and the function that reads a file's size from disk.
"""),

code(f'''
{REMOTE}
OUT = "slo_tmax_2024_monthly.csv"
summary.⟦to_csv⟧(OUT, index=False)
CSV_BYTES = os.path.⟦getsize⟧(OUT)

sizes = pd.DataFrame(
    {{
        "where it lives": ["S3 (NOAA's bucket)", "this machine's RAM", "this machine's disk", "this machine's disk"],
        "size":           [human(SOURCE_BYTES), human(DF_BYTES), human(CSV_BYTES), human(machine_report()["work disk, free (GB)"] * 1e9)],
    }},
    index=["source files", "loaded DataFrame", "exported summary CSV", "free space on the work disk"],
)
sizes
'''),

md("""
**Check yourself.** In one comment: which of those four numbers would also be the size of the file you download to your laptop, and which one disappears when the space stops?
"""),

code(f'''
{REMOTE}
# ⟦The exported summary CSV is what I would download; it is the same few hundred bytes on either disk. The loaded DataFrame lives only in RAM and disappears when the space stops. The source files stay in S3 untouched.⟧
'''),

# ---------------------------------------------------------------- G
md(f"""
## G. Stop the meter

A space bills for every hour its status is *Running*, whether or not you are typing and whether or not this tab is open. A cell cannot stop the machine it is running on, so this happens in the Studio tab.

{STOP_CHECKLIST}

If you are going straight on to the practice activity, leave the space running and do this checklist at the end of that activity instead.
"""),
]


# ======================================================================
# 03 — Practice activity, REMOTE notebook
# ======================================================================
prac_remote = [
md(f"""
# Practice Activity, Remote Notebook: Analyze in the Cloud

**GSB 5544 · Computing and Machine Learning for Business Analytics**

This activity has **two notebooks**. This is the first.

| Notebook | Where you open it | Steps |
|---|---|---|
| `03_practice_activity_remote.ipynb` (this one) | JupyterLab, inside your **SageMaker space** | 1 to 6, and the remote half of Part B |
| `03_practice_activity_local.ipynb` | **Positron**, on your laptop | 7 and 8, and the local half of Part B |

## The workflow

{WORKFLOW_TABLE}

**Part A** (steps 1 to 8) is the real workflow: a remote machine reads ten years of daily high temperatures, about 150 MB of source files and tens of millions of rows, and reduces them to a file small enough to email.

**Part B** is a separate, controlled timing test: the *same* small job run once here and once on your laptop, so the two machines can be compared fairly.

Every code cell starts with a `# RUNS ON:` comment. It names the intended computer. **It does not move the code there.** The setup cell checks where this kernel really is. Cells with `____` have a blank to fill before you run them. If a cell stops with `NameError: name '____' is not defined`, you ran it before filling in its blank; fill the blank and run it again.

By the end you should be able to answer five questions:

{FIVE_QUESTIONS}
"""),

md("""
## Step 1. Sign in to your own AWS account

*You are in: your browser. Code runs: nowhere. Data is: in S3.*

1. Go to [console.aws.amazon.com](https://console.aws.amazon.com) and sign in as **Root user** with the email and password of the account you created in the reading, section 5, part A.
2. On Console Home, read **Credits remaining** in the *Cost and usage* panel and write it down.

## Step 2. Open and start your SageMaker space

*You are in: your browser. Code runs: nowhere yet. Data is: in S3.*

3. In the search bar type **SageMaker AI** and open it. Check the address bar contains `us-east-1`; if not, choose **US East (N. Virginia)** from the region menu at the top right.
4. In the left menu choose **SageMaker Studio**, then click **Open Studio**.
5. In Studio click **JupyterLab**, then click `gsb5544` in the spaces table.
6. Click **Run space** and wait until the status reads **Running**. The meter is now on.
7. Click **Open JupyterLab**. It opens in a new browser tab. This tab is a window onto the remote machine.
8. In JupyterLab's file browser (left side), click the **upload arrow** and upload this notebook, `03_practice_activity_remote.ipynb`. Double-click it to open it **there**.

If you are reading this in Positron, stop: you are in the wrong place for steps 3 to 5. Continue only in the JupyterLab tab.

Run the setup cell. Its last two lines tell you which computer this is.
"""),

code(REMOTE_SETUP),

md("""
Record the remote machine's resources. The local notebook will put your laptop's numbers beside these.
"""),

code(f'''
{REMOTE}
REMOTE_MACHINE = machine_report()
REMOTE_MACHINE
'''),

# ---------------------------------------------------------------- Part A
md("""
# Part A · The workflow

## Step 3. Read NOAA data from S3 into the remote machine

*You are in: the remote notebook. Code runs: on SageMaker. Data moves: S3 → SageMaker's RAM.*

**The data.** NOAA's GHCN-Daily archive, Parquet copy, daily maximum temperature (`TMAX`), one slice per year, 2015 through 2024.

**The subset.** Stations whose id begins `USC0004`: the **California stations of the U.S. Cooperative Observer network**. This is a few hundred volunteer-run stations. It is not every weather station in California, the stations are not evenly spread, and an unweighted average over them is **not** a statewide temperature estimate. It is a consistent, well-defined subset that is the right size for practice.

First, look before you read. Fill in the helper that measures a prefix.
"""),

code(f'''
{REMOTE}
YEARS = list(range(2015, 2025))

SOURCE_BYTES = 0
for year in YEARS:
    objects, size = ⟦prefix_size⟧(slice_prefix(year, "TMAX"))
    SOURCE_BYTES += size
    print(year, f"{{objects:>3}} objects", human(size))

print()
print("Total source size in S3:", human(SOURCE_BYTES))
print("Available RAM here     :", REMOTE_MACHINE["available RAM right now (GB)"], "GB")
'''),

md("""
Ten slices together are much larger in RAM than on disk, and you do not know by how much until you load one. So the plan is: **read one year, summarize it, keep only the summary, then read the next.** Only one year is ever in RAM.

## Step 4. Filter, transform, and aggregate, on the remote machine

*You are in: the remote notebook. Code runs: on SageMaker. Data is: in SageMaker's RAM.*

For each year the function below must:

1. keep the California cooperative stations (`ID` starts with `USC0004`),
2. drop values that failed NOAA's quality checks (`Q_FLAG` is not empty). A dropped or absent value is *missing*, never zero,
3. convert `DATE` to a date and `DATA_VALUE` from tenths of a degree to degrees Celsius,
4. return one row per month: how many stations reported, how many station-days, and the mean daily high.

Fill in the four blanks.
"""),

code(f'''
{REMOTE}
def summarize_year(raw, year):
    keep = raw[raw["ID"].str.startswith(⟦"USC0004"⟧) & raw["Q_FLAG"].⟦isna⟧()].copy()
    keep["date"]   = pd.to_datetime(keep["DATE"].astype(str), format="%Y%m%d")
    keep["tmax_c"] = keep["DATA_VALUE"] / ⟦10⟧
    keep["month"]  = keep["date"].dt.month

    out = (keep.groupby(⟦"month"⟧)
               .agg(stations=("ID", "nunique"),
                    station_days=("tmax_c", "size"),
                    mean_tmax_c=("tmax_c", "mean"))
               .round({{"mean_tmax_c": 2}})
               .reset_index())
    out.insert(0, "year", year)
    return out
'''),

md("""
Now run it for all ten years. This is the heavy part, and the remote machine does all of it. Expect it to take from several seconds to a minute or two; the cell prints one line per year so you can see it working.
"""),

code(f'''
{REMOTE}
pieces = []
ROWS_READ = 0
LARGEST_DF_BYTES = 0

t0 = time.perf_counter()
for year in YEARS:
    raw = pd.read_parquet(
        f"s3://{{BUCKET}}/{{slice_prefix(year, 'TMAX')}}",
        columns=["ID", "DATE", "DATA_VALUE", "Q_FLAG"],
        storage_options={{"anon": True}},
    )
    ROWS_READ += len(raw)
    LARGEST_DF_BYTES = max(LARGEST_DF_BYTES, int(raw.memory_usage(deep=True).sum()))
    pieces.append(summarize_year(raw, year))
    print(f"{{year}}: read {{len(raw):,}} rows")
    del raw                                           # free this year before reading the next
WORKFLOW_SECONDS = time.perf_counter() - t0

summary = pd.concat(pieces, ignore_index=True)
print()
print(f"Read {{ROWS_READ:,}} rows in {{WORKFLOW_SECONDS:.0f}} s. Summary has {{len(summary)}} rows.")
summary.head()
'''),

md("""
## Step 5. Save a small summary CSV on the remote machine

*You are in: the remote notebook. Code runs: on SageMaker. Data moves: SageMaker's RAM → SageMaker's disk.*

The file is written next to this notebook, on the space's own disk. It is not in S3. Fill in the method that writes a CSV.
"""),

code(f'''
{REMOTE}
SUMMARY_FILE = "ca_coop_tmax_monthly_2015_2024.csv"
summary.⟦to_csv⟧(SUMMARY_FILE, index=False)
SUMMARY_BYTES = os.path.getsize(SUMMARY_FILE)

print("Source files in S3      :", human(SOURCE_BYTES))
print("Largest one-year table  :", human(LARGEST_DF_BYTES), "in this machine's RAM")
print("Exported summary CSV    :", human(SUMMARY_BYTES), "on this machine's disk")
print("Free on this work disk  :", machine_report()["work disk, free (GB)"], "GB")
print(f"The summary is about 1/{{SOURCE_BYTES // SUMMARY_BYTES:,}} of the source size.")
'''),

# ---------------------------------------------------------------- Part B
md("""
# Part B · A fair timing test, remote half

Part A cannot be compared with your laptop fairly, because you are not going to run it there. This part can. It is a deliberately small job: **one year (2024), the same four columns, the same filter, the same transformation, the same aggregation**, defined once in `timing_job()` below. The identical function is in the local notebook. Do not edit it in either place.

What it measures, and what it does not:

- **Read seconds** covers fetching the bytes from S3 over the network *and* decoding the Parquet files into a table. On your laptop the network is your home or campus internet; here it is AWS's internal network.
- **Process seconds** covers the filter, the conversions, and the group-by. No network is involved.
- A second run is often faster than the first because parts of the software and the connection are already warm. That is why you run it twice and keep both.
- These are measurements from one moment on two particular machines. Nothing here promises that the cloud is faster.
"""),

code(f'''
{REMOTE}
{TIMING_JOB}
'''),

code(f'''
{REMOTE}
REMOTE_TIMING = []
for run in (1, 2):
    timing_summary, times = timing_job()
    REMOTE_TIMING.append({{"machine": "SageMaker (remote)", "run": run, **times}})
    print(f"run {{run}}: {{times}}")

timing_summary.to_csv("timing_summary_remote.csv", index=False)
'''),

md("""
Now save every measurement from this notebook into one small file, so the local notebook can read them instead of you copying numbers by hand.
"""),

code(f'''
{REMOTE}
measurements = {{
    "machine": REMOTE_MACHINE,
    "workflow": {{
        "years":                   [YEARS[0], YEARS[-1]],
        "source bytes in S3":      SOURCE_BYTES,
        "rows read":               ROWS_READ,
        "largest DataFrame bytes": LARGEST_DF_BYTES,
        "summary CSV bytes":       SUMMARY_BYTES,
        "summary rows":            len(summary),
        "seconds":                 round(WORKFLOW_SECONDS, 1),
    }},
    "timing": REMOTE_TIMING,
}}
with open("remote_measurements.json", "w") as f:
    json.dump(measurements, f, indent=2)

for name in [SUMMARY_FILE, "timing_summary_remote.csv", "remote_measurements.json"]:
    print(f"{{name:<40}} {{human(os.path.getsize(name))}}")
'''),

md(f"""
## Step 6. Download the summary to your laptop

*You are in: the JupyterLab tab's file browser. Code runs: nowhere; your browser copies files. Data moves: SageMaker's disk → your laptop's disk.*

1. In JupyterLab's file browser, click the **refresh arrow**. Three new files appear next to this notebook.
2. Right-click each one and choose **Download**:
   - `ca_coop_tmax_monthly_2015_2024.csv`
   - `timing_summary_remote.csv`
   - `remote_measurements.json`
3. Choose File → **Save Notebook**, then right-click this notebook and **Download** it too. You submit it.
4. On your laptop, **move all four files** from your Downloads folder into your `week_7` folder, the same folder that will hold the local notebook.

## Now switch computers

Leave this browser tab. Open **Positron** on your laptop, open your course folder, and open `03_practice_activity_local.ipynb` from the `week_7` folder. Steps 7 and 8 are there.

Nothing after this point needs the remote machine, so you may stop the space now (step 8 in the local notebook has the checklist). If you leave it running while you work in Positron, it keeps billing.
"""),
]


# ======================================================================
# 03 — Practice activity, LOCAL notebook
# ======================================================================
prac_local = [
md(f"""
# Practice Activity, Local Notebook: Visualize on Your Laptop

**GSB 5544 · Computing and Machine Learning for Business Analytics**

This is the **second** notebook of the practice activity. Open it in **Positron, on your laptop**. Do not upload it to SageMaker.

**Before you start**, your `week_7` folder must contain this notebook and the three files you downloaded in step 6:

- `ca_coop_tmax_monthly_2015_2024.csv`
- `timing_summary_remote.csv`
- `remote_measurements.json`

In Positron: **File → Open Folder** and choose your course folder, then open this notebook from `week_7`. If the notebook asks for a kernel (top right), choose the Python you use for this course.

Every code cell starts with `# RUNS ON: laptop (Positron)`. That comment is a label. It does not move the code. The setup cell checks where this kernel really is. Cells with `____` have a blank to fill before you run them. If a cell stops with `NameError: name '____' is not defined`, you ran it before filling in its blank; fill the blank and run it again.

## The workflow, with the part you have finished

{WORKFLOW_TABLE}

Steps 1 to 6 are done. You are at step 7.
"""),

code(LOCAL_SETUP),

md("""
Check that the three downloaded files are where this notebook can see them.
"""),

code(f'''
{LOCAL}
NEEDED = ["ca_coop_tmax_monthly_2015_2024.csv", "timing_summary_remote.csv", "remote_measurements.json"]
missing = [name for name in NEEDED if not os.path.exists(name)]

print("This notebook is running in:", os.getcwd())
if missing:
    print("MISSING:", missing)
    print("Move them from your Downloads folder into the folder above, then run this cell again.")
else:
    print("All three downloaded files are here.")
    with open("remote_measurements.json") as f:
        REMOTE = json.load(f)
'''),

# ---------------------------------------------------------------- Step 7
md("""
# Part A · The workflow, continued

## Step 7. Open the summary in Positron and make the chart

*You are in: the local notebook, in Positron. Code runs: on your laptop. Data moves: laptop's disk → laptop's RAM.*

The file you are about to read was computed on another computer from data you never downloaded. Fill in the function that reads a CSV.
"""),

code(f'''
{LOCAL}
small = pd.⟦read_csv⟧("ca_coop_tmax_monthly_2015_2024.csv")
DOWNLOADED_BYTES = os.path.getsize("ca_coop_tmax_monthly_2015_2024.csv")

print(small.shape, "read from a file of", human(DOWNLOADED_BYTES))
small.head()
'''),

md("""
Draw one line per year: month on the x-axis, mean daily high on the y-axis. Label the chart for what it is: the **mean of daily highs across reporting California cooperative-network stations**, not a statewide temperature.

Fill in the two column names.
"""),

code(f'''
{LOCAL}
fig, ax = plt.subplots(figsize=(9, 4.5))
for year, rows in small.groupby("year"):
    ax.plot(rows[⟦"month"⟧], rows[⟦"mean_tmax_c"⟧], marker="o", markersize=3, linewidth=1, label=str(year))

ax.set_xticks(range(1, 13))
ax.set_xlabel("Month")
ax.set_ylabel("Mean daily high (°C)")
ax.set_title("California cooperative-network stations: mean daily high by month, 2015–2024")
ax.legend(ncol=2, fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1))
fig.savefig("ca_coop_tmax_monthly.png", dpi=150, bbox_inches="tight")
plt.show()
'''),

md("""
## Two machines, side by side

`machine_report()` measures the computer running this cell: your laptop. The remote machine's numbers come from the file you downloaded. Fill in the function call.
"""),

code(f'''
{LOCAL}
LOCAL_MACHINE = ⟦machine_report⟧()

resources = pd.DataFrame({{"laptop": LOCAL_MACHINE, "SageMaker (remote)": REMOTE["machine"]}})
resources
'''),

md("""
Read the table carefully. "Physical CPU cores" and "logical CPUs" are different things, and a cloud vCPU is a logical CPU. The work-disk rows describe each computer's own disk; neither is S3.

## Four sizes of the same data
"""),

code(f'''
{LOCAL}
w = REMOTE["workflow"]
sizes = pd.DataFrame(
    {{
        "where": ["S3 (NOAA's bucket)", "SageMaker's RAM", "SageMaker's disk", "your laptop's disk"],
        "size":  [human(w["source bytes in S3"]), human(w["largest DataFrame bytes"]),
                  human(w["summary CSV bytes"]), human(DOWNLOADED_BYTES)],
    }},
    index=["source files, ten years", "largest one-year DataFrame", "exported summary CSV", "downloaded summary CSV"],
)
print(f'Rows read remotely: {{w["rows read"]:,}}   Rows in the summary: {{w["summary rows"]}}')
sizes
'''),

# ---------------------------------------------------------------- Part B
md("""
# Part B · A fair timing test, local half

This is the same `timing_job()` as in the remote notebook, character for character: one year, the same columns, the same filter, the same transformation, the same aggregation. Do not edit it.

For this test only, your laptop reads the 2024 slice straight from S3. That is deliberate: both machines must do the same job for the comparison to mean anything. It is a small read. It is **not** the workflow; in the workflow the remote machine did the reading.
"""),

code(f'''
{LOCAL}
{TIMING_JOB}
'''),

code(f'''
{LOCAL}
LOCAL_TIMING = []
for run in (1, 2):
    local_summary, times = timing_job()
    LOCAL_TIMING.append({{"machine": "laptop", "run": run, **times}})
    print(f"run {{run}}: {{times}}")
'''),

md("""
**First, check that both machines computed the same thing.** A timing comparison between two different answers is meaningless. Fill in the file that holds the remote machine's result.
"""),

code(f'''
{LOCAL}
remote_summary = pd.read_csv(⟦"timing_summary_remote.csv"⟧, parse_dates=["date"])

same_shape  = local_summary.shape == remote_summary.shape
same_days   = bool((local_summary["date"].values == remote_summary["date"].values).all()) if same_shape else False
same_counts = bool((local_summary["stations"].values == remote_summary["stations"].values).all()) if same_shape else False
max_gap     = float((local_summary["mean_tmax_c"] - remote_summary["mean_tmax_c"]).abs().max()) if same_shape else float("nan")

print("Same shape          :", same_shape, local_summary.shape, remote_summary.shape)
print("Same dates          :", same_days)
print("Same station counts :", same_counts)
print("Largest difference in mean_tmax_c:", max_gap, "°C")
print("EQUIVALENT" if (same_shape and same_days and same_counts and max_gap < 0.011) else "NOT EQUIVALENT: do not interpret the timings until you know why")
'''),

md("""
If the result is not equivalent, the usual cause is that NOAA updated the archive between your two runs, or that one notebook's `timing_job()` was edited. Rerun both halves close together.

**Then compare the measured times.**
"""),

code(f'''
{LOCAL}
timing = pd.DataFrame(LOCAL_TIMING + REMOTE["timing"]).set_index(["machine", "run"])
timing["total seconds"] = (timing["read seconds"] + timing["process seconds"]).round(2)
timing
'''),

md("""
## Interpret your own results

Answer from the numbers in your tables, not from what you expected. Two or three sentences each.

**T1.** On which machine was **reading** faster, and by how much? Reading includes the network trip from S3 and decoding the files. Which of those do you think explains the difference you saw, given where each computer is?

*Your answer:*

**T2.** On which machine was **processing** faster? Look at the resource table: does the difference in CPUs and RAM account for it?

*Your answer:*

**T3.** Compare run 1 and run 2 on each machine. What changed, and what does that tell you about trusting a single timing?

*Your answer:*

**T4.** For this small job, was the remote machine worth using for speed alone? What would have to be different about the job for your answer to change?

*Your answer:*

# The five questions

Answer each in one or two sentences, with specifics from this activity.

1. **Where is the original data stored?**

   *Your answer:*

2. **Which computer performed the analysis in Part A?**

   *Your answer:*

3. **What did I download, and how big was it compared with what the remote machine read?**

   *Your answer:*

4. **Which computer created the visualization?**

   *Your answer:*

5. **How did the two machines compare, in resources and in measured time?**

   *Your answer:*
"""),

md(f"""
## Step 8. Save your work and stop the remote machine

*You are in: Positron, then your browser. Code runs: nowhere.*

{STOP_CHECKLIST}

A stopped space keeps its disk, so the remote notebook and CSV files are there next time. Its RAM is cleared. You created nothing in S3, so there is nothing to delete there.

## What to submit

Both halves, because the work happened in two places:

1. `03_practice_activity_remote.ipynb`, run in SageMaker, with its output showing.
2. `03_practice_activity_local.ipynb` (this notebook), run in Positron, with its output and your written answers.
3. `ca_coop_tmax_monthly.png`, the chart made on your laptop.
4. A screenshot of the `gsb5544` space page showing status **Stopped**.

The computer names printed by the two setup cells should be different. If they are the same, one of the notebooks was run in the wrong place.
"""),
]


# ======================================================================
# 04 — Lab, REMOTE notebook
# ======================================================================
lab_remote = [
md(f"""
# Lab, Remote Notebook: Weather as a Business Covariate

**GSB 5544 · Computing and Machine Learning for Business Analytics**

You manage inventory planning for a beverage distributor with two markets: **San Luis Obispo, CA** and **Phoenix, AZ**. Before anyone builds a demand model, the team needs each market's recent weather history in a form small enough to share. The raw history sits in NOAA's public S3 bucket, mixed in with every other weather station on Earth.

You will repeat the workflow from the practice activity, with less guidance:

{WORKFLOW_TABLE}

This lab has **two notebooks**. This one runs in **JupyterLab inside your SageMaker space** and covers steps 1 to 6. `04_lab_local.ipynb` runs in **Positron on your laptop** and covers steps 7 and 8, the charts, and the business interpretation.

| Market | Station id | Station name |
|---|---|---|
| San Luis Obispo | `USC00047851` | SAN LUIS OBISPO POLY, CA |
| Phoenix | `USW00023183` | PHOENIX AIRPORT, AZ |

**Rules for this lab**

- All reading from S3 and all summarizing happens **here, on the remote machine**. Downloading raw NOAA files to your laptop and analyzing them there does not satisfy the lab.
- All charts are made **locally, in Positron**. Do not plot in this notebook.
- A missing or quality-flagged observation is **missing**. Never count it as zero.
- No additional AWS services. SageMaker and the public bucket are all you need.

Sign in, start your `gsb5544` space, open JupyterLab, upload this notebook, and open it there (practice activity, steps 1 and 2). Then run the setup cell.
"""),

code(REMOTE_SETUP),

code(f'''
{REMOTE}
STATIONS = {{"San Luis Obispo": "USC00047851", "Phoenix": "USW00023183"}}
YEARS    = list(range(2015, 2025))
ELEMENTS = ["TMAX", "PRCP"]        # daily high (tenths of °C) and daily precipitation (tenths of mm)
'''),

md("""
## L1. The machine you are renting

Store `machine_report()` for this machine as `REMOTE_MACHINE` and display it.
"""),
answer(f'''
{REMOTE}
REMOTE_MACHINE = machine_report()
REMOTE_MACHINE
'''),

md("""
## L2. Size up the job before reading anything

Use `prefix_size()` and `slice_prefix()` to find the size of every slice you need: both elements, all ten years. Print one line per slice and store the total in `SOURCE_BYTES`. Print the total in readable units next to this machine's available RAM.

Then, in the markdown cell: can you tell from these numbers alone whether all of it would fit in RAM at once? What will you do instead?
"""),
answer(f'''
{REMOTE}
SOURCE_BYTES = 0
for element in ELEMENTS:
    for year in YEARS:
        objects, size = prefix_size(slice_prefix(year, element))
        SOURCE_BYTES += size
        print(f"{{element}} {{year}}: {{objects:>3}} objects, {{human(size)}}")

print()
print("Total source size :", human(SOURCE_BYTES))
print("Available RAM here:", REMOTE_MACHINE["available RAM right now (GB)"], "GB")
'''),
md("""
*Your answer:*

"""),

md("""
## L3. Extract both markets

Write `load_market_weather(stations, years, elements)`. For every year and element it reads that one slice from S3, keeps only the stations you asked for, and returns a single tidy DataFrame `wx` with exactly these columns:

| Column | Contents |
|---|---|
| `market` | the market name from `stations` |
| `station_id` | the station id |
| `date` | a real date |
| `element` | `"TMAX"` or `"PRCP"` |
| `value` | the measurement in real units: °C for `TMAX`, mm for `PRCP` (the file stores tenths) |

Requirements:

- Drop rows whose `Q_FLAG` is not empty before anything else.
- Read one slice at a time, and let Parquet do the station filter **during** the read, so that only matching rows reach this machine's RAM. This starter call shows how; `ids` is a list of station ids:

```python
part = pd.read_parquet(
    f"s3://{BUCKET}/{slice_prefix(year, element)}",
    columns=["ID", "DATE", "DATA_VALUE", "Q_FLAG"],
    filters=[("ID", "in", ids)],
    storage_options={"anon": True},
)
```

Call your function, time it, and print how many rows `wx` has for each market and element. Store the elapsed seconds in `EXTRACT_SECONDS` and the DataFrame's memory use in `WX_BYTES`.
"""),
answer(f'''
{REMOTE}
def load_market_weather(stations, years, elements):
    id_to_market = {{station_id: market for market, station_id in stations.items()}}
    ids = list(id_to_market)
    frames = []
    for year in years:
        for element in elements:
            part = pd.read_parquet(
                f"s3://{{BUCKET}}/{{slice_prefix(year, element)}}",
                columns=["ID", "DATE", "DATA_VALUE", "Q_FLAG"],
                filters=[("ID", "in", ids)],
                storage_options={{"anon": True}},
            )
            part = part[part["Q_FLAG"].isna()]
            frames.append(pd.DataFrame({{
                "market":     part["ID"].map(id_to_market),
                "station_id": part["ID"],
                "date":       pd.to_datetime(part["DATE"].astype(str), format="%Y%m%d"),
                "element":    element,
                "value":      part["DATA_VALUE"] / 10,
            }}))
        print("finished", year)
    return pd.concat(frames, ignore_index=True)


t0 = time.perf_counter()
wx = load_market_weather(STATIONS, YEARS, ELEMENTS)
EXTRACT_SECONDS = time.perf_counter() - t0
WX_BYTES = int(wx.memory_usage(deep=True).sum())

print(f"{{len(wx):,}} rows in {{EXTRACT_SECONDS:.0f}} s, {{human(WX_BYTES)}} in RAM")
wx.groupby(["market", "element"]).size()
'''),

md("""
## L4. Hot days per year

For each market and year, count the days with a daily high of **35 °C or higher** (95 °F). Build `hot_days` with one row per market and year and these columns: `market`, `year`, `days_reported`, `hot_days`.

`days_reported` is the number of days that year with a valid `TMAX`. It is there so that a reader can tell a year with few hot days from a year with few *observations*.
"""),
answer(f'''
{REMOTE}
tmax = wx[wx["element"] == "TMAX"].copy()
tmax["year"] = tmax["date"].dt.year
tmax["hot"]  = tmax["value"] >= 35

hot_days = (tmax.groupby(["market", "year"])
                .agg(days_reported=("value", "size"), hot_days=("hot", "sum"))
                .reset_index())
hot_days["hot_days"] = hot_days["hot_days"].astype(int)
hot_days
'''),

md("""
## L5. Monthly rainfall

For each market, find the **typical rainfall of each calendar month**:

1. Total the precipitation for every market, year, and month, and count the days that reported.
2. A monthly total is only trustworthy if nearly every day reported. Keep a month only if at least **90% of its days** have a valid `PRCP` value. (`date.dt.days_in_month` gives the length of a month.) Discarding an incomplete month is different from treating its missing days as dry.
3. Average the kept monthly totals over the years.

Build `monthly_rain` with twelve rows per market and these columns: `market`, `month`, `years_used`, `avg_monthly_prcp_mm` (rounded to 1 decimal).
"""),
answer(f'''
{REMOTE}
prcp = wx[wx["element"] == "PRCP"].copy()
prcp["year"]  = prcp["date"].dt.year
prcp["month"] = prcp["date"].dt.month
prcp["days_in_month"] = prcp["date"].dt.days_in_month

by_month = (prcp.groupby(["market", "year", "month"])
                .agg(total_mm=("value", "sum"),
                     days_reported=("value", "size"),
                     days_in_month=("days_in_month", "first"))
                .reset_index())
complete = by_month[by_month["days_reported"] >= 0.9 * by_month["days_in_month"]]

monthly_rain = (complete.groupby(["market", "month"])
                        .agg(years_used=("year", "nunique"), avg_monthly_prcp_mm=("total_mm", "mean"))
                        .round({{"avg_monthly_prcp_mm": 1}})
                        .reset_index())
print("Months dropped as incomplete:", len(by_month) - len(complete), "of", len(by_month))
monthly_rain
'''),

md("""
## L6. Export, and record what happened here

Save the two summaries on this machine's disk as `lab_hot_days.csv` and `lab_monthly_rain.csv`. Then write `lab_remote_measurements.json` containing a dictionary with:

- `"machine"`: `REMOTE_MACHINE`
- `"source bytes in S3"`: `SOURCE_BYTES`
- `"rows kept"`: the number of rows in `wx`
- `"DataFrame bytes"`: `WX_BYTES`
- `"extract seconds"`: `EXTRACT_SECONDS`, rounded
- `"exported bytes"`: the combined size on disk of the two CSV files

Print the size of each of the three files.
"""),
answer(f'''
{REMOTE}
hot_days.to_csv("lab_hot_days.csv", index=False)
monthly_rain.to_csv("lab_monthly_rain.csv", index=False)

measurements = {{
    "machine":            REMOTE_MACHINE,
    "source bytes in S3": SOURCE_BYTES,
    "rows kept":          len(wx),
    "DataFrame bytes":    WX_BYTES,
    "extract seconds":    round(EXTRACT_SECONDS, 1),
    "exported bytes":     os.path.getsize("lab_hot_days.csv") + os.path.getsize("lab_monthly_rain.csv"),
}}
with open("lab_remote_measurements.json", "w") as f:
    json.dump(measurements, f, indent=2)

for name in ["lab_hot_days.csv", "lab_monthly_rain.csv", "lab_remote_measurements.json"]:
    print(f"{{name:<32}} {{human(os.path.getsize(name))}}")
'''),

md("""
## L7. What did this session cost?

Estimate the compute cost of this session: hours the space has been running, times the hourly price of its instance type. Use about **$0.05 per hour** for `ml.t3.medium` in `us-east-1`, and check the [SageMaker pricing page](https://aws.amazon.com/sagemaker/ai/pricing/) if you chose a different instance. Reading NOAA's public bucket from inside the same region adds no data-transfer charge, and you created nothing in S3.

The starter below tries to read the space's start time. If that lookup fails, set `hours` by hand from the time you clicked **Run space**.
"""),
code(f'''
{REMOTE}
import datetime as dt

PRICE_PER_HOUR = 0.05            # ml.t3.medium, us-east-1, approximate; change it if your instance type differs

try:
    meta = json.load(open("/opt/ml/metadata/resource-metadata.json"))
    sm = boto3.client("sagemaker", region_name=REGION)
    app = sm.describe_app(DomainId=meta["DomainId"], SpaceName=meta["SpaceName"],
                          AppType=meta["AppType"], AppName=meta["ResourceName"])
    hours = (dt.datetime.now(dt.timezone.utc) - app["CreationTime"]).total_seconds() / 3600
except Exception as e:
    print("Could not read the space's start time:", type(e).__name__)
    hours = ⟦1.0⟧                  # <- set by hand: hours since you clicked Run space

print(f"Running for about {{hours:.2f}} h  ×  ${{PRICE_PER_HOUR}}/h  =  ${{hours * PRICE_PER_HOUR:.3f}}")
'''),

md("""
## Download, then switch computers

1. In JupyterLab's file browser click the refresh arrow, then right-click and **Download** each of:
   `lab_hot_days.csv`, `lab_monthly_rain.csv`, `lab_remote_measurements.json`.
2. File → **Save Notebook**, then download this notebook too.
3. Move all four files into your lab folder on your laptop, next to `04_lab_local.ipynb`.
4. Open **Positron** and continue in `04_lab_local.ipynb`.

Nothing after this point needs the remote machine. Stop the space now, or at the end of the local notebook, but do stop it.
"""),
]


# ======================================================================
# 04 — Lab, LOCAL notebook
# ======================================================================
lab_local = [
md("""
# Lab, Local Notebook: Visualize and Interpret

**GSB 5544 · Computing and Machine Learning for Business Analytics**

Open this notebook in **Positron, on your laptop**. It needs the three files you downloaded from your SageMaker space, in the same folder as this notebook:

- `lab_hot_days.csv`
- `lab_monthly_rain.csv`
- `lab_remote_measurements.json`

Everything here runs on your laptop. No cell in this notebook reads from S3.
"""),

code(LOCAL_SETUP),

code(f'''
{LOCAL}
NEEDED = ["lab_hot_days.csv", "lab_monthly_rain.csv", "lab_remote_measurements.json"]
missing = [name for name in NEEDED if not os.path.exists(name)]
print("This notebook is running in:", os.getcwd())
print("MISSING: " + ", ".join(missing) if missing else "All three downloaded files are here.")
'''),

md("""
## L8. Read what you downloaded

Read the two CSV files into `hot_days` and `monthly_rain`, and the JSON file into `REMOTE`. Print each table's shape and the size on disk of each downloaded file.
"""),
answer(f'''
{LOCAL}
hot_days     = pd.read_csv("lab_hot_days.csv")
monthly_rain = pd.read_csv("lab_monthly_rain.csv")
with open("lab_remote_measurements.json") as f:
    REMOTE = json.load(f)

print("hot_days    :", hot_days.shape)
print("monthly_rain:", monthly_rain.shape)
for name in NEEDED:
    print(f"{{name:<32}} {{human(os.path.getsize(name))}}")
'''),

md("""
## L9. Chart 1: hot days per year

One line per market: year on the x-axis, number of days at or above 35 °C on the y-axis. Label both axes with units, give the chart a title that says what it shows, and save it as `lab_hot_days.png`.

Before you plot, look at `days_reported`. If any market-year has far fewer than 365 reported days, say so in your interpretation in L11.
"""),
answer(f'''
{LOCAL}
print(hot_days.pivot(index="year", columns="market", values="days_reported"))

fig, ax = plt.subplots(figsize=(9, 4))
for market, rows in hot_days.groupby("market"):
    ax.plot(rows["year"], rows["hot_days"], marker="o", linewidth=1.3, label=market)
ax.set_xticks(sorted(hot_days["year"].unique()))
ax.set_xlabel("Year")
ax.set_ylabel("Days with a high of 35 °C or more")
ax.set_title("Hot days per year, 2015–2024")
ax.grid(alpha=0.3)
ax.legend()
fig.savefig("lab_hot_days.png", dpi=150, bbox_inches="tight")
plt.show()
'''),

md("""
## L10. Chart 2: typical rainfall by month

Show the average monthly precipitation for both markets across the twelve calendar months, in millimeters, in a form that makes the two markets easy to compare. Save it as `lab_monthly_rain.png`. Then print the wettest month of each market.
"""),
answer(f'''
{LOCAL}
wide = monthly_rain.pivot(index="month", columns="market", values="avg_monthly_prcp_mm")

ax = wide.plot(kind="bar", figsize=(9, 4), width=0.8)
ax.set_xlabel("Calendar month")
ax.set_ylabel("Average monthly precipitation (mm)")
ax.set_title("Typical rainfall by month, complete months of 2015–2024")
ax.grid(axis="y", alpha=0.3)
ax.figure.savefig("lab_monthly_rain.png", dpi=150, bbox_inches="tight")
plt.show()

print("Wettest month:", wide.idxmax().to_dict())
'''),

md("""
## L11. The business read

Answer as the inventory planner, in six to eight sentences, using numbers from your two charts.

- How differently should the two markets be stocked across the year? Refer to both heat and rain.
- Is there anything in `days_reported` or `years_used` that should make the team cautious about a particular year or month?
- Name **two** other datasets you would want to join to this weather history before trusting a demand model, and say where each one probably lives: on a laptop, in a company database, or in cloud storage.

*Your answer:*

"""),

md("""
## L12. Two machines and four sizes

Build one table that puts your laptop's `machine_report()` beside the remote machine's (from `REMOTE["machine"]`). Then print, in readable units: the source size in S3, the size of the remote DataFrame, the combined size of the exported CSVs, and the combined size of the files as downloaded on this laptop.
"""),
answer(f'''
{LOCAL}
resources = pd.DataFrame({{"laptop": machine_report(), "SageMaker (remote)": REMOTE["machine"]}})
print(resources)
print()
downloaded = os.path.getsize("lab_hot_days.csv") + os.path.getsize("lab_monthly_rain.csv")
print("Source files in S3       :", human(REMOTE["source bytes in S3"]))
print("Remote DataFrame in RAM  :", human(REMOTE["DataFrame bytes"]), f'({{REMOTE["rows kept"]:,}} rows)')
print("Exported CSVs, remote    :", human(REMOTE["exported bytes"]))
print("Downloaded CSVs, laptop  :", human(downloaded))
print("Remote extract took      :", REMOTE["extract seconds"], "s")
'''),

md(f"""
## L13. Where the work happened

**(a)** Answer each of the five questions in one or two sentences, with specifics from this lab.

{FIVE_QUESTIONS}

*Your answers:*

**(b)** This weather summary will be refreshed **every week** once the demand model is live. Would you run the weekly refresh on your laptop or on a SageMaker space? Give two reasons that use what you measured: the source size, the size of what comes home, the resources of each machine, and the cost from L7.

*Your answer:*

## L14. Save and stop

{STOP_CHECKLIST}

Paste a screenshot of the `gsb5544` space page showing status **Stopped** into the cell below, or submit it as a separate image.

*Evidence:*

## What to submit

1. `04_lab_remote.ipynb`, run in SageMaker, with output showing.
2. `04_lab_local.ipynb` (this notebook), run in Positron, with output and written answers.
3. `lab_hot_days.csv` and `lab_monthly_rain.csv`.
4. `lab_hot_days.png` and `lab_monthly_rain.png`.
5. The screenshot showing the space **Stopped**.

A submission is graded on both halves. A lab whose charts were made on SageMaker, or whose summaries were computed on a laptop, has not done the workflow.
"""),
]


# ======================================================================
# 05 — Optional Athena extension (remote)
# ======================================================================
athena = [
md("""
# Optional Extension: Athena

**GSB 5544 · Not part of the required first session**

Everything required in Session 1 runs on SageMaker alone. This notebook is for later, or for the curious. Read the **Athena extension guide** on the course site first. It explains what Athena is, the **one-time permission step** this notebook needs, what it costs, and how to clean up.

Athena is a query service. You send it SQL; AWS's own machines scan Parquet files in S3 and write the answer to a bucket **you** own. So this notebook, unlike the others, creates something in your account (a results bucket) and can incur a small per-query charge.

Run it in JupyterLab inside your SageMaker space. Cells with `____` have a blank to fill before you run them. If a cell stops with `NameError: name '____' is not defined`, you ran it before filling in its blank; fill the blank and run it again.
"""),

code(REMOTE_SETUP),

code(f'''
{REMOTE}
import io

STATIONS = {{"San Luis Obispo": "USC00047851", "Phoenix": "USW00023183"}}
STATION  = STATIONS["San Luis Obispo"]
BY_YEAR_2024_BYTES = s3.head_object(Bucket=BUCKET, Key="csv/by_year/2024.csv")["ContentLength"]
print("The 2024 by-year CSV is", human(BY_YEAR_2024_BYTES))
'''),

md("""
## 1. A results bucket you own

Athena writes every result to S3, so you need a bucket of your own. These clients are **signed**: they act as you, because this bucket is yours, not public. If this cell stops with `AccessDenied`, the permission step in the extension reading has not been done.

Fill in the bucket name in the create call.
"""),

code(f'''
{REMOTE}
sts     = boto3.client("sts",    region_name=REGION)
athena  = boto3.client("athena", region_name=REGION)
s3_mine = boto3.client("s3",     region_name=REGION)

ACCOUNT        = sts.get_caller_identity()["Account"]
RESULTS_BUCKET = f"gsb5544-athena-{{ACCOUNT}}"     # bucket names are global, so include your account id
RESULTS        = f"s3://{{RESULTS_BUCKET}}/athena/"

s3_mine.create_bucket(Bucket=⟦RESULTS_BUCKET⟧)   # in us-east-1 no LocationConstraint is needed
print("Results will land in", RESULTS)
'''),

md("""
## 2. Helpers and a table definition

`run_athena` starts a query, checks once a second until it finishes, and returns the query id plus Athena's statistics, which include the bytes scanned. The table definition tells Athena where the Parquet files are and how the `YEAR=`/`ELEMENT=` key layout maps to columns (this is called *partition projection*). Nothing is copied, and these definition statements are free.

Fill in the `boto3` call that starts a query.
"""),

code(f'''
{REMOTE}
ATHENA_BYTES = 0                                  # running total of everything scanned today

def run_athena(sql, database=None):
    """Start a query, wait for it, return (query id, statistics)."""
    global ATHENA_BYTES
    kwargs = {{"QueryString": sql, "ResultConfiguration": {{"OutputLocation": RESULTS}}}}
    if database:
        kwargs["QueryExecutionContext"] = {{"Database": database}}
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
    """Read a finished query's result CSV from the results bucket."""
    obj = s3_mine.get_object(Bucket=RESULTS_BUCKET, Key=f"athena/{{qid}}.csv")
    return pd.read_csv(io.BytesIO(obj["Body"].read()))
'''),

code(f'''
{ATHENA}
run_athena("CREATE DATABASE IF NOT EXISTS gsb5544")

DDL = \'\'\'
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
    'storage.location.template' = 's3://noaa-ghcn-pds/parquet/by_year/YEAR=${{year}}/ELEMENT=${{element}}/'
)
\'\'\'
run_athena(DDL, database="gsb5544")
print("Table gsb5544.ghcn is defined. Bytes scanned so far:", human(ATHENA_BYTES))
'''),

md("""
## 3. One station, one year

The `WHERE` clause is the extraction. Fill in the year and the name of the statistic that reports bytes scanned.
"""),

code(f'''
{ATHENA}
SQL = f\'\'\'
SELECT id, "date", data_value
FROM   gsb5544.ghcn
WHERE  year = ⟦2024⟧
  AND  element IN ('TMAX', 'PRCP')
  AND  q_flag IS NULL
  AND  id = '{{STATION}}'
\'\'\'

qid, stats = run_athena(SQL, database="gsb5544")
scanned = stats["⟦DataScannedInBytes⟧"]
station_2024 = athena_df(qid)

print(f"Rows returned : {{len(station_2024):,}}")
print(f"Bytes scanned : {{human(scanned)}}")
print(f"Query time    : {{stats['TotalExecutionTimeInMillis'] / 1000:.1f}} s")
print(f"Cost          : ${{max(scanned, 10_000_000) / 1e12 * 5:.4f}}   (about $5 per TB scanned, 10 MB minimum; check the Athena pricing page)")
print(f"2024 CSV is   : {{human(BY_YEAR_2024_BYTES)}}")
station_2024.head()
'''),

md("""
Athena scanned far less than the by-year CSV. Which feature of the bucket's layout let it skip every other year and element before reading a row? One sentence, as a comment.
"""),

code(f'''
{REMOTE}
# ⟦The YEAR=/ELEMENT= key layout. Athena treats those as partition columns, so the WHERE clause on year and element selects which files to open, and the other years and elements are never read.⟧
'''),

md("""
## 4. Hot days, computed entirely by Athena

Write **one query** that returns the number of days with `TMAX` at or above 35 °C (`data_value >= 350`) per station per year from 2015 through 2024, for both lab stations, ignoring quality-flagged values. Pivot the result to years as rows and markets as columns. It should match the `hot_days` table from the lab.
"""),
answer(f'''
{ATHENA}
SQL = f\'\'\'
SELECT id, year, COUNT(*) AS hot_days
FROM   gsb5544.ghcn
WHERE  element = 'TMAX'
  AND  year BETWEEN 2015 AND 2024
  AND  q_flag IS NULL
  AND  id IN ('{{STATIONS["San Luis Obispo"]}}', '{{STATIONS["Phoenix"]}}')
  AND  data_value >= 350
GROUP BY id, year
ORDER BY year, id
\'\'\'

qid, stats = run_athena(SQL, database="gsb5544")
id_to_market = {{v: k for k, v in STATIONS.items()}}

hot_athena = (
    athena_df(qid)
    .assign(market=lambda d: d["id"].map(id_to_market))
    .pivot(index="year", columns="market", values="hot_days")
    .fillna(0).astype(int)
)
print(f"Athena scanned {{human(stats['DataScannedInBytes'])}} for this query")
hot_athena
'''),

md("""
A station-year with no row in this result had no day at or above 35 °C *among the days it reported*. The `fillna(0)` in the pivot is correct for a count of hot days, but it cannot tell you whether the station reported all year. The lab's `days_reported` column exists for that reason.

## 5. Clean up: empty the results bucket

Unlike the required session, this notebook created something in S3 that stays after the space stops. Empty it. Fill in the call that lists the bucket and the call that deletes a batch of objects.
"""),

code(f'''
{REMOTE}
listing = s3_mine.⟦list_objects_v2⟧(Bucket=RESULTS_BUCKET)
objects = listing.get("Contents", [])
print(f"{{len(objects)}} result objects, {{human(sum(o['Size'] for o in objects))}}")

if objects:
    s3_mine.⟦delete_objects⟧(Bucket=RESULTS_BUCKET, Delete={{"Objects": [{{"Key": o["Key"]}} for o in objects]}})

print("Bucket empty :", "Contents" not in s3_mine.list_objects_v2(Bucket=RESULTS_BUCKET))
print("Athena today :", human(ATHENA_BYTES), f"scanned, about ${{max(ATHENA_BYTES, 10_000_000) / 1e12 * 5:.4f}}")
'''),

md(f"""
Then stop the space, as always.

{STOP_CHECKLIST}
"""),
]


# ======================================================================
R = {REMOTE}
L = {LOCAL}
RA = {REMOTE, ATHENA}

import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Solutions are written here, next to the student notebooks (they are part of the course site),
# and a copy is placed in the instructor's course folder when that folder exists.
INSTRUCTOR_COPY = Path("/Users/immanuelwilliams/Library/CloudStorage/OneDrive-Personal/Documents/Important_Files/Cal_Poly/01_Class_Material/GSB_5544/gsb5544_instructor_learn_prep/assignments/practice_activities/week_7/aws_content")

for cells, stem, allowed in [
    (topics,      "02_topics_of_practice",       R),
    (prac_remote, "03_practice_activity_remote", R),
    (prac_local,  "03_practice_activity_local",  L),
    (lab_remote,  "04_lab_remote",               R),
    (lab_local,   "04_lab_local",                L),
    (athena,      "05_athena_extension",         RA),
]:
    build(cells, str(HERE / f"{stem}.ipynb"), student=True, allowed=allowed)
    build(cells, str(HERE / f"{stem}_SOLUTIONS.ipynb"), student=False, allowed=allowed)
    if INSTRUCTOR_COPY.exists():
        shutil.copy2(HERE / f"{stem}_SOLUTIONS.ipynb", INSTRUCTOR_COPY / f"{stem}_SOLUTIONS.ipynb")

print(f"built 12 notebooks in {HERE}")
if INSTRUCTOR_COPY.exists():
    print(f"copied the 6 solution notebooks to {INSTRUCTOR_COPY}")
