---
title: "Changelog: Session 1, local compute to remote compute"
---

**Date:** 2026-09-26
**Scope:** the six files in `session_1/`. Originals are preserved in git history (commit `12e5b34` and earlier).

## Summary

As originally written, AWS was only the storage side of Session 1: students pulled files from the public `noaa-ghcn-pds` bucket, but every `read_csv`, filter, `groupby`, and plot ran on their laptop. This revision moves the computation onto AWS while keeping the pedagogy that already worked. Two services are used and nothing else:

1. **Amazon SageMaker Studio (JupyterLab space)** on an `ml.t3.medium` in `us-east-1`. The same notebooks run there; the laptop becomes a browser tab.
2. **Amazon Athena** over `s3://noaa-ghcn-pds/parquet/by_year/`, queried from the notebook with `boto3`. This is "filter at the source" taken to its conclusion: the `WHERE` clause runs on AWS's fleet.

The module now teaches three things about AWS explicitly: **space** (what storage costs and that it has no practical ceiling), **ability** (that compute is rented by the hour in sizes you choose), and **cost** (per-hour, per-byte, and the difference between a notebook that is open and a space that is running). Cost is graded: the practice activity ends with a cost audit and a verified teardown.

## Assumptions made (please review)

The prompt left two fields for the instructor to fill in. Neither was filled, so these choices were made and should be confirmed before the session:

- **Environment: AWS Academy Learner Lab.** Chosen because it is the standard for university courses and removes account creation, credit cards, and IAM setup. Consequences: the reading's walkthrough starts with "Start Lab"; the execution role is `LabRole`; the cost audit reads the Learner Lab budget readout rather than Cost Explorer (which the Learner Lab hides); teardown ends with "End Lab." A callout in the reading covers the personal-account path (budget alarm first) so the material works for either. **Verify in your Learner Lab** that SageMaker Studio domain creation is permitted (some Learner Lab variants restrict SageMaker), that `LabRole` allows Athena and the Glue Data Catalog (`CREATE DATABASE`, `CREATE EXTERNAL TABLE`), and that it allows `sagemaker:DescribeApp` and `sagemaker:ListApps` (used in Q13).
- **Region: `us-east-1`**, the GHCN bucket's region. The reading explains co-location; every client is created with this region explicitly.
- **Athena from `boto3` directly**, not `awswrangler`. The notebooks define a 20-line `run_athena()` helper (`start_query_execution`, poll `get_query_execution`, return statistics) and `athena_df()` (read the result CSV from the results bucket). Reason: no new dependency, the same library students already know, and the fact that results land in S3 stays visible instead of being hidden by a wrapper.
- **Results bucket name: `gsb5544-athena-<account id>`**, derived at runtime from STS, so there is nothing to configure per student and no name collisions.
- **Table definition:** external table `gsb5544.ghcn` with **partition projection** (`year` integer 1750–2030, `element` enum of `TMAX,TMIN,PRCP,SNOW,SNWD,TAVG`). Projection avoids `MSCK REPAIR TABLE`, which would crawl roughly 270 year prefixes × 100 element prefixes. The Parquet schema was verified against a live file in the bucket on 2026-09-26: `ID string, DATE string (YYYYMMDD), DATA_VALUE bigint, M_FLAG, Q_FLAG, S_FLAG, OBS_TIME string`. The column `date` is a reserved word, so it is backticked in DDL and double-quoted in `SELECT`; the notebooks say so.
- **Prices** (approximate, `us-east-1`, labelled as such in the reading and linked to the pricing pages): `ml.t3.medium` $0.05/h, `ml.t3.xlarge` $0.20/h, `ml.m5.4xlarge` $0.92/h, `ml.m5.24xlarge` $5.53/h; Athena $5/TB scanned with a 10 MB minimum, DDL free; S3 Standard $0.023/GB-month; transfer out $0.09/GB after 100 GB/month free; Studio EBS $0.10/GB-month. Check these against the pricing pages before teaching.
- **`s3fs`**: both setup cells run `%pip install -q s3fs` because I could not confirm it ships in the SageMaker Distribution image. It is harmless if already present. Everything else (`boto3`, `pandas`, `psutil`, `matplotlib`) does ship.
- **Not executed against a live account.** The notebooks were not run on AWS from here. Every solution cell compiles (enforced by the build script), the bucket layout and Parquet schema were checked against the live public bucket, and the `boto3` calls follow the documented API. The Athena DDL, the `/opt/ml/metadata/resource-metadata.json` lookup in Q13(b), and the Learner Lab permissions need **one dry run in the actual lab** before class.

## `01_preclass_reading.md`

- **Front matter and intro.** Reframed from "storage is remote, compute is yours" to "storage and compute are both things you rent." Introduced the three questions (space, ability, cost) that the module now asks repeatedly. The list of what the reading gives you grew from three items to four (the fourth: run the same notebook next to the data and know what it costs).
- **§1 What your machine actually has.** Kept. Added `# RUNS ON: laptop` to the cell, the instruction to write all five numbers down, and a blank two-column table (laptop now / SageMaker in class) that block A of the topics notebook and Q1 of the practice activity fill in.
- **§2 The units of data.** Kept verbatim, including the file-size-vs-memory multiplier. The closing sentence now says the two remedies are a smaller extraction or a bigger machine, and to try the free one first.
- **§3 The vocabulary of AWS.** Added the two required rows, **Instance type** (with `ml.t3.medium` and its hourly price) and **Athena**. Table now has eleven terms. Closing paragraph now says compute is rented too, and can be a laptop, an instance for the afternoon, or a fleet for eight seconds.
- **§4 Where does the code run? (new).** Defines *kernel*, *instance*, and *region co-location*. Introduces the `# RUNS ON:` convention with its three exact values. Adds an "ability" table of four instance types with cores, RAM, and hourly price. Walks through opening a SageMaker Studio JupyterLab space in the Learner Lab in eight steps, with the `psutil` cell as the first thing to run, and step 8 being Stop. Callout for personal accounts (budget alarm first).
- **§5 Reading from S3 without an account** (was §4). Kept. Added that unsigned reads work identically inside SageMaker, that the SageMaker image already has the libraries, a short paragraph introducing the `parquet/` prefix and its `YEAR=`/`ELEMENT=` layout, and the observation that an `ml.t3.medium` cannot open a by-year CSV either, so renting did not change the arithmetic. `# RUNS ON:` lines on every cell.
- **§6 Extraction strategy** (was §5). Kept levers 1 to 3 and the station-file pattern. The by-year chunked read is now **timed** and students are told to write down `LAPTOP_SECONDS` for Q11. Added **"The fourth lever: let the fleet do the filtering"** with the SQL that block J runs and an explanation of why Parquet plus partitioned keys makes it cheap. Units trap kept.
- **§7 Cost, space, and ability (new, required).** Three tables: space (S3 storage, requests, transfer in and out of region, EBS), ability (two instance types and Athena), and the "open is not running" worked examples (3 h = $0.15; a forgotten weekend = $3.20; a forgotten month = $36; same month on a 16-core box = $662). Ends with the four-step teardown habit.
- **"Where this goes next"** (old §6) was replaced by **"Before class: what to bring"**: the five laptop numbers, `LAPTOP_SECONDS`, and a lab that has been started once so the domain exists.
- **Reading check.** Kept all five questions; added #6 on region co-location.
- **References.** Added Athena `boto3` reference, SageMaker Studio spaces docs, SageMaker, Athena, and S3 pricing pages, and Athena partition projection.

## `build_notebooks.py`

- Docstring documents the `# RUNS ON:` convention. Three allowed values are the set `RUNS_ON_VALUES`.
- `answer()` student output now keeps the cell's first line (the `# RUNS ON:` line) above `# your code here`, so students see where the empty cell will run.
- `build()` gained two checks: every code cell in every notebook must begin with one of the three exact `# RUNS ON:` lines (build aborts otherwise), and the solutions compile check now strips IPython `%`/`!` lines first so `%pip install` can live in the setup cell.
- The `# RUNS ON:` line is written literally as the first line of every cell source, not added by post-processing, so it survives regeneration.
- `⟦...⟧` and `answer()` conventions unchanged.

## `02_topics_of_practice.ipynb` (11 blocks, was 9 plus a closing cell)

- **Intro.** Says to run the notebook inside the SageMaker space, explains the `# RUNS ON:` line, and asks students to bring their laptop numbers. Removed "No AWS account is required."
- **Setup cell.** Runs on SageMaker. Added `%pip install -q s3fs`, `import time`, and `REGION = "us-east-1"`.
- **Block A → "Two machines, side by side."** Still fill-in-the-blank (`virtual_memory`, `available`). Now stores this machine's numbers in a dict, a second cell takes the laptop's numbers and builds a comparison DataFrame with a ratio column (blank: the dict to compare against), and a reflection cell asks why rent a machine that is smaller than your laptop.
- **Blocks B–I.** Unchanged logic; `# RUNS ON: SageMaker …` added to every cell; section references renumbered to the new reading (§5, §6, §7). Block C's vocabulary check gained **instance type** and **Athena**. Block E now saves `BY_YEAR_2024_BYTES` for block J. Block E's fit check says "on this ml.t3.medium." Block G notes the bytes never touch the laptop.
- **Block J "Ask Athena for the same station" (new).** Four code cells: signed clients and results bucket creation (blank: the bucket name in `create_bucket`); the `run_athena`/`athena_df` helpers with an `ATHENA_BYTES` running total (blank: `start_query_execution`); the `CREATE DATABASE` and `CREATE EXTERNAL TABLE` DDL (runs on Athena, no blanks); and the query for the block G station, 2024, `TMAX`+`PRCP` (blanks: the year in the `WHERE` clause and `DataScannedInBytes`). Prints rows, bytes scanned, seconds, estimated cost, and the ratio against the 1.3 GB CSV from block E. A reflection cell asks which lever the partition layout pulled.
- **Block K "Stop the meter" (new).** Empties the results bucket (blanks: `list_objects_v2`, `delete_objects`), prints the day's Athena bytes and cost, then a checklist for stopping the space in the Studio UI and ending the lab. The old "Before you leave" reflection was folded in here and extended with "what did Athena add."

## `03_practice_activity.ipynb` (13 questions, was 11)

- **Intro.** Says to run inside SageMaker, explains `# RUNS ON:`, and notes that Q1 and Q11 need numbers from the reading. "Run the two setup cells first."
- **Setup cell.** Runs on SageMaker. Added `%pip install -q s3fs`, `json`, `datetime`, `REGION`. `human()`, `COLS`, `STATIONS`, and the unsigned client are unchanged.
- **Athena setup cell (new, given).** Same code as block J: signed clients, results bucket, helpers with `ATHENA_BYTES`, `CREATE DATABASE`, `CREATE EXTERNAL TABLE`. Given rather than asked so Q11 to Q13 test the SQL and the comparison, not the boilerplate.
- **Q1 → "Two machines."** One DataFrame with a column per machine; laptop column holds the numbers from the reading. Added a one-sentence markdown answer on which machine to use for a 1.3 GB read.
- **Q2, Q3, Q5.** Unchanged logic; wording now says "this machine's" RAM.
- **Q4, Q7, Q8, Q9.** Unchanged apart from the `# RUNS ON:` line.
- **Q6.** Unchanged logic. Prompt now says it runs on SageMaker and the bytes never touch the laptop.
- **Q10.** Kept both original bullets. Added the required sentence: which of the three compute tiers the planner would choose for a weekly refresh and why, with a note to revise after Q11. Length guidance raised from four-to-six to five-to-seven sentences.
- **Set 5 "Where the work runs" (new heading).**
- **Q11 → three-tier timing.** (a) laptop seconds pasted from the reading; (b) the same chunked read on SageMaker, timed; (c) Athena, timed, bytes scanned recorded. Builds a `race` DataFrame and confirms the row count against the by-station path from Q6. Written answer must use "filter at the source" and say what changed a→b and b→c. The old Q11 was this exercise's laptop-only version.
- **Q12 (new).** One Athena query with `GROUP BY id, year` for hot days from 2015 onward, pivoted and checked against Q7's `hot`. Prints Athena bytes scanned beside the bytes pandas read in Q6. The written answer asks students to notice that Athena over `by_year` scans *more* bytes than reading the two by-station CSVs, and to say when each path wins.
- **Q13 (new, graded).** (a) empty the results bucket; (b) estimate today's spend from the space's start time (`describe_app` via the Studio metadata file, with a manual fallback) and `ATHENA_BYTES`; (c) stop the space in the UI; (d) evidence: screenshot of *Stopped* plus the budget readout, or a verification cell that runs on the laptop and lists SageMaker apps and their status.
- **Submission note.** Now lists Q1, Q4, Q10, Q11, Q12 written answers plus Q13 evidence, and says a submission is not complete while its space is running.

## Both solutions notebooks

Regenerated from the build script. Every solution code cell compiles. Header detection (`Range="bytes=0-99"` then `startswith("ID,")`) is unchanged and is used in block G, Q6, and Q11(b).

## Preserved exactly

- `human()` and its base-1000 behavior.
- Station IDs `USC00047851` and `USW00023183`; the "size first, always" habit (`head_object` before `get_object`).
- The `⟦...⟧` blank convention and `answer()` in the build script.
- `"YE"` / `"ME"` resample aliases with the pandas < 2.2 comment.
- All five original reading-check questions.
- The unsigned `boto3` client for listing and metadata.

## Final checks run

- Every code cell in both student notebooks begins with a `# RUNS ON:` line (build-time assertion; 22 + 16 cells).
- No cell assumes a header row in the GHCN CSVs.
- No reference to SageMaker Studio Lab or S3 Select in any file.
- The practice activity ends with teardown (Q13); the reading ends with cost (§7) before the pre-class checklist and reading check.
- `build_notebooks.py` runs without error and regenerates all four notebooks.
