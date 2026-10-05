---
title: "Optional Extension: Athena, a Fourth Place a Filter Can Run"
---

**GSB 5544 · Optional. Not part of the required first session.**

*Everything required in Session 1 runs on SageMaker alone. This guide and its notebook, `05_athena_extension.ipynb`, preserve the Athena material for a later session or for students who want to go further. Do the required reading, topics notebook, and practice activity first.*

::: {.callout-warning title="Read this before you start"}
This extension differs from the required work in three ways:

- It needs a **one-time permission change** in your account (part 2 below).
- It **creates a bucket in your account** that stays until you empty it.
- It can incur a **small per-query charge** against your credits.

The steps below were written for the course but have **not been run end to end in a student Free plan account**. If a step does not match what you see, stop and ask; do not upgrade your plan to get past it.
:::

---

## 1. Where Athena fits

In the required workflow there are two computers: your laptop and your SageMaker space. The filter and the summary run on the SageMaker space, and only a small file comes home.

**Amazon Athena** is a third place the work can run. It is a query service: you send it a SQL statement, AWS's own machines scan Parquet files directly in S3, and the answer is written as a CSV into a bucket you own. You do not start, size, or stop those machines. You pay for the bytes the query had to scan.

| | Stores data? | Runs code? | You pay for |
|---|---|---|---|
| S3 bucket | Yes | No | GB stored per month |
| SageMaker space | A little | Yes, your Python | Hours it is *Running* |
| **Athena** | No. It reads from S3 and writes its answer to S3 | Yes, SQL only, on AWS-managed machines | Bytes scanned per query |

```sql
-- RUNS ON: Athena (AWS-managed)
SELECT id, "date", data_value
FROM   ghcn
WHERE  year = 2024 AND element = 'TMAX' AND id = 'USC00047851'
```

**What this code does.**

- `SELECT id, "date", data_value` names the three columns to return. Parquet stores each column separately, so the others are never read.
- `FROM ghcn` refers to a *table definition* that the notebook creates. It tells Athena that the Parquet files under `parquet/by_year/` should be treated as one table. Nothing is copied.
- `WHERE year = 2024 AND element = 'TMAX'` picks which *files* Athena opens, and `id = 'USC00047851'` picks which *rows* inside them it returns.

Two things make this cheap. Parquet is columnar, so Athena reads only the columns named. And the `YEAR=2024/ELEMENT=TMAX/` layout of the keys lets Athena open only that one slice and skip every other year and element. Telling Athena how that key layout maps to columns is called **partition projection**; the notebook's table definition does it.

In the required session you already use the same two ideas from pandas: you read one year-and-element slice, and you ask for only the columns you need. Athena moves that work off your instance entirely.

---

## 2. One-time setup: let your Studio role use Athena

The Quick setup in the reading gives your SageMaker space permission to use SageMaker and little else. The Athena notebook also needs to run Athena queries and to create, read, and empty a results bucket. You add those permissions once, in the console.

1. In the console search bar type **IAM** and open it. In the left menu choose **Roles**.
2. In the search box type `AmazonSageMaker`. Click the role the Quick setup created; its name begins with **AmazonSageMaker** and contains **ExecutionRole**. If more than one appears, open JupyterLab on your space, run the cell below in a new notebook, and use the role name it prints.

```python
# RUNS ON: SageMaker (remote)
import boto3
print(boto3.client("sts").get_caller_identity()["Arn"].split("/")[1])
```

3. On the role's page choose **Add permissions → Attach policies**. Search for and tick **AmazonAthenaFullAccess**, then search for and tick **AmazonS3FullAccess**. Click **Add permissions**.
4. Both policies now appear in the role's list. There is nothing to restart.

These are broad permissions, chosen so that setup is two ticks and not a custom policy. They apply only inside your own account.

---

## 3. Running the notebook

Open `05_athena_extension.ipynb` in **JupyterLab on your SageMaker space**. Three computers take part:

1. **Your laptop** is only the browser tab.
2. **Your SageMaker instance** runs the notebook cell, which hands the SQL text to Athena with `boto3` and waits.
3. **Athena's machines** scan the Parquet files in NOAA's bucket and write the answer into your results bucket. The notebook then reads that small CSV into pandas.

| Section of the notebook | What it does | What you should see |
|---|---|---|
| 1. Results bucket | Creates a bucket named `gsb5544-athena-` plus your 12-digit account number | `Results will land in s3://gsb5544-athena-…/athena/` |
| 2. Helpers and table | Defines `run_athena` (start a query, poll once a second until it finishes, add up bytes scanned) and `athena_df` (read a result). Creates a database `gsb5544` and a table `ghcn` that points at the Parquet files | `Table gsb5544.ghcn is defined. Bytes scanned so far: 0.0 B` |
| 3. One station, one year | Sends the `SELECT` above for the SLO station, for `TMAX` and `PRCP` | Rows returned, bytes scanned, query time, estimated cost |
| 4. Hot days by Athena | One query that reproduces the lab's hot-days table | A year-by-market table |
| 5. Clean up | Deletes the result files from your bucket | `Bucket empty : True` |

Running any cell a second time is safe: the bucket, database, and table are created only if they do not already exist.

::: {.callout-warning title="If a cell fails"}
- **`AccessDeniedException`** or **`not authorized to perform: athena:…`**: the permission step in part 2 has not been done, or was applied to the wrong role. The role to change is the one named in the error message.
- **`Unable to verify/create output bucket`**: the results-bucket cell did not run, or ran in a different region. Rerun it.
- **`NameError`**: the kernel restarted. Run the notebook again from the top.
- **`TABLE_NOT_FOUND`** or **`SCHEMA_NOT_FOUND`**: the table-definition cell did not finish. Rerun it.
:::

::: {.callout-tip title="Optional: watch the same query in the Athena console"}
After the notebook has run once, type **Athena** in the console search bar and open **Query editor**. The first time, a banner asks for a result location: click **Edit settings** and enter `s3://gsb5544-athena-` followed by your account number and `/athena/`. Pick the database **gsb5544**; the table **ghcn** appears beneath it. Paste the `SELECT` statement, click **Run**, and read **Data scanned** under the result. The **Recent queries** tab lists every query your notebook sent.
:::

---

## 4. Cost and cleanup

- **Athena** charges per byte scanned, with a small minimum per query; definition statements (`CREATE ...`) and failed queries are not charged. The notebook estimates each query's cost at about $5 per TB with a 10 MB minimum, which was the published rate when this was written. Check the [Athena pricing page](https://aws.amazon.com/athena/pricing/) for the current rate. The queries here scan megabytes, so each costs a small fraction of a cent.
- **The results bucket** is real storage in your account, charged per GB per month, and it is **not** removed when your space stops. Section 5 of the notebook empties it. Run it every time.
- **The space** bills per hour while *Running*, exactly as in the required session. Stop it when you finish.

## 5. A caution about comparing speeds

An earlier version of these materials raced a laptop, a SageMaker instance, and Athena against each other. That comparison was not fair: the three were doing different amounts of work on different copies of the data, and the laptop time was an extrapolation. If you compare Athena with pandas, compare **what each one had to read** (bytes scanned versus source bytes) and report measured times as measurements from one moment, not as a ranking. The required practice activity shows what a controlled timing comparison looks like.

## References

- Athena pricing: <https://aws.amazon.com/athena/pricing/>
- Athena partition projection: <https://docs.aws.amazon.com/athena/latest/ug/partition-projection.html>
- boto3 Athena client reference: <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/athena.html>
