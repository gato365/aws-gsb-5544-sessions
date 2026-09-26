---
title: "Pre-Class Reading: Data Bigger Than Your Laptop"
---

**GSB 5544 · Computing and Machine Learning for Business Analytics**

*Read before class and run the code as you go, on your laptop. In class you will run the same code on a machine you rent from AWS and put the two side by side. The practice activity assumes you have done both.*

---

## Why this matters for a business analyst

Every dataset you have used in this course so far arrived as a file you opened. That is not how data arrives in practice. The sales history, the clickstream, the sensor log, the claims table: they live somewhere else, they are usually larger than your machine, and someone has to decide *what to bring over* before any modeling begins.

There is a second decision hiding behind the first one: *where should the code run?* Until now the answer was always "on my laptop," because that was the only computer you had. In the cloud, **storage and compute are both things you rent.** The data sits in a bucket. The computer that reads it can be your laptop, a rented machine sitting in the same building as the bucket, or a fleet of machines that runs one SQL statement and hands you back only the rows that matched.

Every cloud decision comes down to three questions, and you will ask them repeatedly in this module:

- **Space.** How much data is there, and where does it live?
- **Ability.** How much computer do I need to work on it, and for how long?
- **Cost.** What does that space and ability cost per hour, per gigabyte, per query?

This reading gives you four things:

1. A way to measure what a machine can hold, so you can compare your laptop to a rented one.
2. The vocabulary to describe the size of data and the parts of a cloud system.
3. A working pattern for reading only what you need from a large remote dataset.
4. A way to run the same notebook on a machine next to the data, and to know what it costs.

We will use weather data as the example. Weather is one of the most common external covariates in business analytics: it drives beverage and apparel demand, energy load, insurance claims, delivery times, and foot traffic. It is also a dataset that is far too large to open on a laptop, which is exactly the point.

---

## 1. What your machine actually has

Your laptop has an amount of memory (RAM) installed, and a smaller amount that is *available right now*. The available number is the one that determines whether a dataset loads. Measure it:

```python
# RUNS ON: laptop
import psutil

vm = psutil.virtual_memory()
du = psutil.disk_usage("/")

print(f"Physical cores : {psutil.cpu_count(logical=False)}")
print(f"Logical cores  : {psutil.cpu_count(logical=True)}")
print(f"Total RAM      : {vm.total / 1e9:.1f} GB")
print(f"Available RAM  : {vm.available / 1e9:.1f} GB")   # the number that matters
print(f"Free disk      : {du.free / 1e9:.1f} GB")
```

**Write all five numbers down.** In class you will run this exact cell a second time inside a rented AWS machine and put the two columns next to each other. The lesson of that comparison is the lesson of the whole module: *the machine running your code is a choice, and you can change it.*

| | Laptop (now) | SageMaker (in class) |
|---|---|---|
| Physical cores | | |
| Logical cores | | |
| Total RAM (GB) | | |
| Available RAM (GB) | | |
| Free disk (GB) | | |

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
# RUNS ON: laptop
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
# RUNS ON: laptop
df.memory_usage(deep=True).sum()   # deep=True, or string columns are undercounted
```

So the question "does this fit?" is really: *is (file size × a multiplier) less than my available RAM?* When the answer is no, you have two choices, and this module teaches both. You can make a **smaller extraction**, or you can rent a **bigger machine**. Usually you do the first before the second, because the first is free.

---

## 3. The vocabulary of AWS

Amazon Web Services is the largest cloud provider, and its vocabulary has become the industry's vocabulary. Eleven terms cover most of what you will read in documentation, pricing pages, and error messages.

| Term | What it is | The confusion it prevents |
|---|---|---|
| **Region** | A geographic cluster of data centers (`us-east-1`, `us-west-2`) | Why a bucket "doesn't exist": you are looking in the wrong region |
| **S3** | Simple Storage Service. Object storage, not a filesystem | Why there are no real folders, only names that contain slashes |
| **Bucket** | A named container for objects. Names are globally unique across all of AWS | Why `my-data` is already taken by a stranger |
| **Object** | One stored item plus its metadata (size, last modified, type) | Why you can read an object's size without downloading it |
| **Key** | The object's full name within the bucket, e.g. `csv/by_year/2024.csv` | Why that is one string, not three folders and a file |
| **Prefix** | The start of a key, used to list "everything under" something | How S3 fakes folders |
| **EC2** | Elastic Compute Cloud. A rented virtual computer | What "compute" means as distinct from "storage" |
| **Instance type** | The size of a rented computer: cores, RAM, and a price per hour. `ml.t3.medium` is 2 cores, 4 GB, about $0.05 per hour | Why "run it in the cloud" is not one thing; you choose how much machine |
| **Athena** | A SQL engine that runs a query across many machines directly against files in S3 and bills per byte scanned | How a `WHERE` clause can run on AWS's fleet instead of on your machine |
| **IAM** | Identity and Access Management. Who may do what | Why code gets `AccessDenied` even on public data |
| **Credentials** | The keys that identify you to AWS | Why "unsigned" or "anonymous" requests exist, and when you need to sign one |

The single most important idea underneath all eleven: **storage and compute are separate, and both are rented.** Data sits in S3. Computers reach into S3 for it. The computer can be your laptop, an instance you rent for the afternoon, or a fleet you rent for eight seconds. The data does not move; you decide what reaches for it.

---

## 4. Where does the code run?

Three definitions, then a walkthrough.

**Kernel.** The process that actually executes your notebook cells. When you press Shift-Enter, the browser sends the cell to a kernel and the kernel sends back the output. The browser and the kernel do not have to be on the same computer. So far in this course they have been.

**Instance.** A rented computer with a fixed number of cores and a fixed amount of RAM, billed by the hour while it is running. When you run a notebook in Amazon SageMaker Studio, the kernel lives on an instance in an AWS data center, and your laptop becomes a browser tab.

**Region co-location.** Putting the instance in the same region as the bucket. The GHCN bucket is in `us-east-1`, so our instances are in `us-east-1`. Inside one region, S3 and the instance are connected by AWS's own network: reads are fast and the data transfer is free. Across the public internet to your laptop, the same read is slower and, past a free allowance, AWS charges for every gigabyte that leaves. Same code, same file, different bill.

### The `# RUNS ON:` convention

From here on, **every code cell in this module starts with a comment that says where it executes.** There are exactly three values:

```python
# RUNS ON: laptop
# RUNS ON: SageMaker ml.t3.medium (us-east-1)
# RUNS ON: Athena fleet (results land in S3)
```

The habit matters more than the syntax. An analyst who cannot say where a piece of code runs cannot say what it costs, how long it will take, or why it failed.

### How much machine: the ability you are renting

An instance type is a menu item. Prices are approximate, for `us-east-1`, at the time of writing; the SageMaker pricing page has the current numbers.

| Instance type | Cores | RAM | Approx. price per hour | Comparable to |
|---|---|---|---|---|
| `ml.t3.medium` | 2 | 4 GB | $0.05 | A budget laptop; our default |
| `ml.t3.xlarge` | 4 | 16 GB | $0.20 | A good laptop |
| `ml.m5.4xlarge` | 16 | 64 GB | $0.92 | A workstation |
| `ml.m5.24xlarge` | 96 | 384 GB | $5.53 | A server rack you would never buy for one project |

Read the table two ways. First, a bigger machine is one dropdown away and costs dollars per hour, not thousands up front. Second, the small one is enough for almost everything in this module, because the reading pattern in section 6 keeps the data small. Rent ability when extraction is not enough, not instead of it.

### Getting onto AWS: a free account and a SageMaker Studio space

This module runs on AWS through a **free AWS account**. A new account starts on AWS's **Free Plan**: you receive $100 of credits that last six months, everything you run spends from those credits, and when the credits or the six months run out the account is paused rather than billed. Nothing in this module comes close to spending them if you stop your machine when you finish. The console changes its labels from time to time; follow the on-screen names if they differ slightly from these.

Do parts A through C **before class**, ideally a few days before. Account activation and the one-time SageMaker setup each take several minutes, and you do not want to be waiting on them while everyone else is running code.

#### Part A. Create the free account (once)

1. **Go to** [aws.amazon.com/free](https://aws.amazon.com/free) and click **Create a free account**. Use an email address you will still have next year. Give the account a name; any name works, and it appears in the top-right corner of the console afterwards.
2. **Verify the email and fill in your details.** AWS emails a verification code, then asks for a root-user password, your name, address, and phone number. Choose **Personal** as the account type.
3. **Payment card.** AWS asks for a card to confirm your identity. On the Free Plan the card is not charged; the credits are the only thing that gets spent. If you are asked to choose between a **Free** and a **Paid** plan, choose **Free**. A phone verification follows: AWS texts or calls you with a code.
4. **Sign in** at [console.aws.amazon.com](https://console.aws.amazon.com) as the *root user*, with the email and password you just set. A brand-new account can take a few minutes to activate; if sign-in fails right away, wait and try again.

#### Part B. Read the Console Home before you click anything

The first page after sign-in is **Console Home**. It is busy. Three things on it matter for this module; ignore the rest, including Amazon Q, the "Recently visited" panel, and any banners.

![Console Home on a new Free Plan account. The **Cost and usage** panel at the bottom shows the credits and days remaining; the region and account name sit in the top-right corner (blurred here).](images/console-home.png){fig-alt="AWS Console Home showing the Amazon Q panel, an empty Recently visited panel, and a Cost and usage panel reading $100.00 credits remaining and 182 days remaining."}

- **Cost and usage**, lower on the page. It shows **Credits remaining** (starts at $100.00) and **Days remaining** (starts near 182). This panel is your budget and your timer. The practice activity asks you to read these numbers before and after class, so **write both down now**.
- **Region**, in the top-right corner next to your account name. It must read **US East (N. Virginia)**, which is `us-east-1`. If it says anything else, click it and choose N. Virginia. The GHCN data lives in `us-east-1`; this is the co-location from the definitions above, and it also decides which price list you are on.
- **The search bar** at the top. It is how you reach every service. Type a service name, press Enter, and pick the service (not the documentation link) from the results.

#### Part C. Set up SageMaker Studio (once)

5. In the search bar type **SageMaker AI** and open it. There is also a plain "SageMaker" entry; the one you want is **SageMaker AI**.
6. In the left menu, under *Applications and IDEs*, choose **SageMaker Studio**. On a new account the page shows a **Get Started** box with the button **Create a SageMaker domain**. Click it.

![The SageMaker Studio page on a new account. Click **Create a SageMaker domain** in the Get Started box.](images/05-sagemaker-landing.png){fig-alt="Amazon SageMaker AI console with SageMaker Studio selected in the left menu and a Get Started box containing the Create a SageMaker domain button."}
7. On the **Set up SageMaker domain** page, leave **Set up for single user (Quick setup)** selected and click **Set up** in the lower right. AWS creates a *domain* (the container for your Studio settings and files) and an *execution role* (the permissions your rented machine will have; the page calls it a new IAM role). Do not choose the organizations option.

![Set up for single user (Quick setup) is the left card and is selected by default. The **Set up** button is in the lower right.](images/06-quick-setup.png){fig-alt="Set up SageMaker domain page with two cards, Set up for single user Quick setup selected, and an orange Set up button."}
8. A progress page appears while the domain is created. Keep the tab open until it finishes; the page says about 20 seconds, but allow a few minutes. When it lands you in Studio, the one-time setup is done. If instead you see a message that SageMaker is **not available on your plan**, stop here and tell me before class so we can arrange an alternative. Do not upgrade the plan on your own.

![The setup progress page. Leave it open until the bar reaches 100%.](images/07-domain-setting-up.png){fig-alt="Amazon SageMaker Studio setup page listing what gets created, with a progress bar at 32 percent."}

#### Part D. Create and run the JupyterLab space (each session)

9. Studio opens on its own **Home** page, a dark interface that looks nothing like the rest of the console. On later days, reach it from the SageMaker Studio page by clicking **Open Studio**. Under **Applications** in the top-left, click **JupyterLab**.

![Studio Home. JupyterLab is the first tile under Applications and also the large orange card.](images/08-studio-home.png){fig-alt="SageMaker Studio Home page with Applications tiles for JupyterLab, Canvas, Code Editor and MLflow, and a large JupyterLab card."}
10. The JupyterLab page lists your spaces; on the first visit it says *No JupyterLab spaces*. Ignore the **Space templates** and their *Launch now* links, which create a space with a generated name. Instead click **Create JupyterLab space** in the top right.

![The JupyterLab spaces page before any space exists. Use **Create JupyterLab space**, top right.](images/09-jupyterlab-spaces.png){fig-alt="JupyterLab page in SageMaker Studio showing three space templates, an empty spaces table, and a Create JupyterLab space button."}
11. In the dialog, name the space `gsb5544`, leave **Private** selected, and click **Create space**.

![The Create JupyterLab space dialog with the name filled in.](images/09-create-space.png){fig-alt="Create JupyterLab space dialog with Name set to gsb5544 and Sharing set to Private."}
12. The space's own page opens with status *Stopped*. Check three settings before you run it. **Instance** should read `ml.t3.medium` and **Image** should read *SageMaker Distribution* (the version number does not matter). Further down, change **Idle Shutdown (minutes)** from its default of 10080 (a week) to **60**, so a space you forget turns itself off after an hour. Leave **Storage** at 5 GB. Then click **Run space**.

![The space page before running. Instance and Image are at the top; Idle Shutdown is in the Space Settings panel below.](images/10-space-settings.png){fig-alt="SageMaker Studio space page for gsb5544 showing a Run space button, status Stopped, Instance ml.t3.medium, Image Sagemaker Distribution 4.5.0, and space settings including Idle Shutdown of 10080 minutes."}
13. The status changes to *Starting* and a banner estimates the remaining time. It takes one to three minutes. When it reads *Running*, the **Run space** button becomes **Open JupyterLab**; click it. **The billing clock starts at *Running*.**

![The space starting. Wait for the status to read Running.](images/10-space-starting.png){fig-alt="The gsb5544 space page with status Starting and a banner reading Starting space, estimated time remaining 30 seconds."}
14. JupyterLab opens in a new tab. It is the same JupyterLab you have used on your laptop, except that the kernel now lives on the rented instance and your laptop is a browser tab. **Upload the two notebooks** for this session with the upload arrow in the left file browser, open the topics-of-practice notebook, and **run the `psutil` cell first**, before anything else. Fill in the right-hand column of the table in section 1.

#### Part E. Stop the space when you are done (every time)

15. Go back to the Studio tab, open **JupyterLab** in the left menu, find `gsb5544` in the spaces table, click **Stop**, and wait until the status reads **Stopped**. A stopped space keeps your files and costs a few cents a month for storage. A running space costs the same whether or not you are typing.
16. Return to **Console Home** and read **Credits remaining** again. Compare it with the number you wrote down in part B. A class session should show 15 to 30 cents of difference, sometimes zero because the panel updates with a delay. The practice activity ends with a graded shutdown check for exactly this reason.

::: {.callout-tip title="Lab, space, instance, domain: which word is which"}
- **Instance**: the rented computer, such as `ml.t3.medium`. It has the cores and RAM from the table above, and it bills by the hour while it runs.
- **Space**: SageMaker's name for one JupyterLab environment plus its storage. A space *runs on* an instance. The space is the thing you **Run** and **Stop**.
- **Domain**: the one-time Studio setup that holds your spaces and permissions. You create it once and never touch it again.
- **Learner Lab**: the classroom sandbox that AWS Academy gives to some courses. If you created your own free account, you do not have a lab, and there is no **Start Lab** button anywhere. Go straight to SageMaker.
:::

::: {.callout-note title="If you upgrade to a paid plan later"}
The Free Plan cannot run up a bill: when the credits are gone, the account pauses. A paid account can. Before you create anything on a paid account, set a **budget alarm**: in the search bar type *Billing*, open **Budgets**, choose **Create budget**, pick a monthly *cost* budget of $10, and add an email alert at 80%. Everything in this module costs under a dollar if you stop the space when you finish; the alarm is there for the day you forget.
:::

::: {.callout-note title="If your course provides the AWS Academy Learner Lab instead"}
Some courses supply accounts through [AWS Academy](https://aws.amazon.com/training/awsacademy/), reached from a Canvas course rather than from a sign-up page; your instructor sends the invitation, and there is no card. The Learner Lab account is temporary and has a fixed budget and a session timer. The differences from the steps above: skip part A. Open the Learner Lab page, click **Start Lab**, wait for the circle next to "AWS" to turn green, and click the green **AWS** link to open the console. The **budget** and **timer** at the top of the lab page replace Console Home's credits and days in part B. In part C, if the Quick setup offers a choice of execution role, pick the existing **LabRole** instead of creating one. In part E, after stopping the space, also click **End Lab** on the lab page.
:::

---

## 5. Reading from S3 without an account

Many large public datasets are hosted on S3 through the [Registry of Open Data on AWS](https://registry.opendata.aws/). They can be read *anonymously*: no account, no credit card, no credentials. The request is simply not signed. This works identically from your laptop and from inside SageMaker; only the network in between changes.

Install what you need on your laptop (once). Inside SageMaker the default image already has all of these.

```bash
pip install boto3 s3fs psutil pandas matplotlib
```

`boto3` is the official AWS library for Python. Create an unsigned client:

```python
# RUNS ON: laptop
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
# RUNS ON: laptop
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

The `parquet/` prefix contains the same data a third time, in a columnar format that SQL engines can read selectively. Its keys look like `parquet/by_year/YEAR=2024/ELEMENT=TMAX/…parquet`. That `YEAR=`/`ELEMENT=` pattern is not decoration; section 6 shows what it buys you.

### Reading a size without reading the file

Every object carries its size as metadata. You can read it for free:

```python
# RUNS ON: laptop
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

Compare that to your available RAM from section 1, and remember the multiplier. One year of GHCN is a file most laptops cannot open with a plain `pd.read_csv`. Notice that an `ml.t3.medium`, with 4 GB, cannot open it either. Renting a machine did not change the arithmetic; only extraction or a much larger instance does.

For a single object, `head_object` returns the metadata alone:

```python
# RUNS ON: laptop
meta = s3.head_object(Bucket=BUCKET, Key="csv/by_year/2024.csv")
meta["ContentLength"], meta["LastModified"]
```

### Reading a *slice* of a file

S3 supports HTTP range requests, so you can read the first few hundred bytes of a gigabyte file to see its shape:

```python
# RUNS ON: laptop
obj = s3.get_object(Bucket=BUCKET, Key="csv/by_year/2024.csv", Range="bytes=0-299")
print(obj["Body"].read().decode())
```

Use this to check whether a file has a header row before you read it. If the first line begins with `ID,`, it does. Never assume either way; the check costs 300 bytes.

---

## 6. Extraction strategy: filter at the source

When data does not fit, there are three levers, and they all express one principle: **move the filter to the data instead of moving the data to the filter.**

**Lever 1: pick the right object.** GHCN offers the same data by year (1.3 GB, all stations) and by station (a few MB, all years). If you need one location, read the station file. Choosing the object is the cheapest filter there is.

**Lever 2: read fewer columns.** `usecols` tells pandas to discard columns while parsing, so they never take memory.

**Lever 3: read fewer rows at a time.** `chunksize` returns an iterator of DataFrames; you filter each chunk and keep only what survives.

Here is the pattern, reading one station directly from S3. The GHCN CSV columns are, in order: station ID, date (YYYYMMDD), element code, value, and four flag columns.

```python
# RUNS ON: laptop
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

For a by-year file, add lever 3 and keep only the rows you want as they stream past. **Time this one and write the number down.** It is the laptop leg of a three-way race you will finish in class, and it is the slow leg, so run it now while you read the rest of this page. Expect several minutes; if your connection is very slow, note how long you waited before giving up, and bring that number instead.

```python
# RUNS ON: laptop
import time

key = "csv/by_year/2024.csv"
first = s3.get_object(Bucket=BUCKET, Key=key, Range="bytes=0-99")["Body"].read().decode()
has_header = first.upper().startswith("ID,")

t0 = time.perf_counter()
chunks = pd.read_csv(
    f"s3://{BUCKET}/{key}",
    storage_options={"anon": True},                 # unsigned, via s3fs
    header=0 if has_header else None,
    names=COLS,
    usecols=["id", "date", "element", "value"],
    chunksize=1_000_000,                            # lever 3
)
keep = pd.concat(c[c["id"] == STATION] for c in chunks)
LAPTOP_SECONDS = time.perf_counter() - t0

print(f"{len(keep):,} rows for {STATION} in {LAPTOP_SECONDS:,.0f} s")   # write this down
```

Both produce the same rows for that station. One reads 6.7 MB; the other reads 1.3 GB and throws almost all of it away. Lever 1 was the one that mattered.

### The fourth lever: let the fleet do the filtering

There is one more place a filter can run: on AWS's own machines, before anything reaches yours at all. **Amazon Athena** takes a SQL statement, runs it across many machines directly against the Parquet files in S3, writes the result to a bucket you own, and charges you for the bytes it had to scan. A `WHERE` clause becomes the extraction.

```sql
-- RUNS ON: Athena fleet (results land in S3)
SELECT id, "date", data_value
FROM   ghcn
WHERE  year = 2024 AND element = 'TMAX' AND id = 'USC00047851'
```

Two things make this cheap. Parquet is columnar, so Athena reads only the columns named. And the `YEAR=2024/ELEMENT=TMAX/` layout of the keys means Athena opens only that one slice of the bucket and never touches the other 270 years or the other 100-odd element codes. In class you will run this query from the notebook with `boto3`, read the bytes-scanned statistic, and compare it to the 1.3 GB CSV. Levers 1 to 3 shrink what *your* machine reads. Lever 4 shrinks what *any* machine reads.

### The units trap

GHCN stores temperatures in **tenths of a degree Celsius** and precipitation in **tenths of a millimeter**. A `TMAX` value of `266` means 26.6 °C. Divide by 10 before you do anything else, or your first chart will show 300-degree days. Data arrives with conventions attached; reading the documentation is part of extraction.

```python
# RUNS ON: laptop
df["date"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d")
tmax = df[df["element"] == "TMAX"].copy()
tmax["tmax_c"] = tmax["value"] / 10
```

---

## 7. Cost, space, and ability: what you are actually renting

Cost is part of the job, not a footnote. A model that costs more to refresh than the decision it informs is a bad model. Here is what the three things in this module cost, approximately, in `us-east-1` at the time of writing. Check the pricing pages in the references for current numbers.

### Space: storing data

| What | Approx. price | What it means for you |
|---|---|---|
| S3 Standard storage | $0.023 per GB per month | 1 GB of query results for a month: about 2 cents. The 100+ GB GHCN bucket is paid for by the AWS Open Data program, not by you |
| S3 requests | $0.005 per 1,000 writes/lists, $0.0004 per 1,000 reads | Every `list_objects_v2`, `head_object`, and `get_object` in this module together: well under a cent |
| Data transfer S3 → your laptop | First 100 GB per month free, then $0.09 per GB | Reading the 1.3 GB by-year file at home twenty times a month starts to cost real money |
| Data transfer S3 → SageMaker, same region | Free | The reason for co-location |
| SageMaker space storage (EBS) | $0.10 per GB per month | A stopped space with the default 5 GB volume: about 50 cents a month |

There is no practical ceiling on space. A single S3 object can be 5 TB; a bucket can hold as many objects as you pay for. Space is almost never the constraint. Ability and cost are.

### Ability: renting compute

| What | Approx. price | What it means for you |
|---|---|---|
| `ml.t3.medium` (2 cores, 4 GB) | $0.05 per hour | A three-hour class session: 15 cents |
| `ml.m5.4xlarge` (16 cores, 64 GB) | $0.92 per hour | Enough to open a whole by-year CSV in pandas. An hour of it costs less than a coffee |
| Athena | $5 per TB scanned, 10 MB minimum per query. DDL statements and failed queries are free | The largest query in this module scans about 600 MB: a third of a cent |

The point of the second table: ability is rented in hours, not bought in years. If a job needs 64 GB of RAM once a quarter, you rent 64 GB for that hour. Your laptop is not the ceiling on what you can analyze; it is just the machine you happen to be typing on.

### Open is not running

This is the single most expensive misunderstanding in cloud computing, so read it twice.

- A notebook that is **open in your browser** costs nothing. It is a text file being displayed.
- A JupyterLab space whose status is **Running** costs its hourly price every hour, whether or not a notebook is open, whether or not you are typing, whether or not you have closed the browser tab.
- A space whose status is **Stopped** costs only its storage, a few cents a month.

Two worked examples with the `ml.t3.medium` price:

| Scenario | Hours | Cost |
|---|---|---|
| Class session, then Stop | 3 | $0.15 |
| Forgot to stop it Friday, noticed Monday | 64 | $3.20 |
| Forgot for a month | 720 | $36.00 |
| Same month, `ml.m5.4xlarge` | 720 | $662.40 |

On the Free Plan, **Credits remaining** on Console Home is what stands between you and the last row. When it reaches zero the account is paused, and the material you have not downloaded goes with it. In the Learner Lab, the budget at the top of the lab page plays the same role. On a paid plan, the budget alarm from section 4 is the only guard.

### The teardown habit

Every session on a rented machine ends the same way, in this order, and the practice activity grades it:

1. Empty the results bucket you created for Athena, so no stray gigabytes accumulate.
2. Stop the JupyterLab space and watch the status change to *Stopped*.
3. Look at the budget or the billing page and confirm the number is what you expected.
4. End the lab.

Analysts who do this by reflex are trusted with cloud accounts. Analysts who do not, are not.

---

## Before class: what to bring

- The five laptop numbers from section 1, filled into the left column of the table.
- `LAPTOP_SECONDS` from section 6, or how long you waited before giving up.
- Your free AWS account created (section 4, part A), signed into once, and the **Credits remaining** and **Days remaining** from Console Home written down (part B).
- SageMaker Studio set up once (part C), so the domain already exists and you are not waiting on it in class. Creating and running the space (part D) can wait until class, but running it once beforehand and stopping it again (part E) is a good rehearsal.

---

## Reading check

Answer these for yourself before class. They are the first questions in the practice activity.

1. Your machine reports 16 GB total and 4.2 GB available. A CSV is 1.3 GB on disk. Will `pd.read_csv` on the whole file probably succeed? Show the arithmetic.
2. What is the difference between a bucket, a key, and a prefix? Give one example of each from `noaa-ghcn-pds`.
3. Why can `list_objects_v2` tell you a file's size without downloading it?
4. You need every temperature reading for Phoenix since 1990. Which object do you read: `csv/by_year/*.csv` or `csv/by_station/USW00023183.csv`? Why?
5. A `TMAX` value in the file is `412`. What is the temperature in Celsius? In Fahrenheit?
6. Why does it matter that the notebook and the bucket are in the same region? Name one effect on speed and one on cost.

---

## References

- Registry of Open Data on AWS — NOAA GHCN-D: https://registry.opendata.aws/noaa-ghcn/
- GHCN-D by-year file format (column order and units): https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme-by_year.txt
- GHCN-D full readme (element codes, flags): https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt
- boto3 S3 client reference: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
- boto3 Athena client reference: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/athena.html
- pandas `read_csv` (`usecols`, `chunksize`, `storage_options`): https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
- SageMaker Studio JupyterLab spaces: https://docs.aws.amazon.com/sagemaker/latest/dg/studio-updated-jl.html
- SageMaker pricing (instance types): https://aws.amazon.com/sagemaker/pricing/
- Athena pricing: https://aws.amazon.com/athena/pricing/
- Athena partition projection: https://docs.aws.amazon.com/athena/latest/ug/partition-projection.html
- S3 pricing: https://aws.amazon.com/s3/pricing/
