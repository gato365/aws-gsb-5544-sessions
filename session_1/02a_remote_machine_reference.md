---
title: "Remote Machine Reference"
---

**GSB 5544 · Session 1 · companion to the topics notebook**

This page records what the course's SageMaker space actually reports about itself, so that students can check their own numbers against a known-good run, and so that the instance type, memory, and disk in the materials match what students will really see.

## How the numbers were obtained

1. Sign in to AWS, start the `gsb5544` space, and open JupyterLab (reading, section 5, parts D and E).
2. Upload and open `02_topics_of_practice.ipynb`, run the setup cell, then run block A.
3. Block A's last cell writes `remote_machine_report.md` next to the notebook and prints it. Right-click the file in JupyterLab's file browser and choose **Download**.
4. Paste the file's contents into the section below, replacing the placeholder table.

Two other places show details about the space without running code:

- **The space page in Studio** (JupyterLab → `gsb5544`): instance type, image and version, storage size, and idle-shutdown setting.
- **The JupyterLab tab's address bar**: the domain id and the region appear in the URL.

## Instructor's run

*Replace this table with the contents of `remote_machine_report.md` from your own run, and note the date.*

| Measure | Value |
|---|---|
| space name | gsb5544 |
| instance type (from the space page) | ml.t3.medium |
| image (from the space page) | SageMaker Distribution |
| storage (from the space page) | 5 GB |
| idle shutdown (from the space page) | 60 minutes |
| computer name | *not yet recorded* |
| physical CPU cores | *not yet recorded* |
| logical CPUs (vCPUs in the cloud) | *not yet recorded* |
| total RAM (GB) | *not yet recorded* |
| available RAM right now (GB) | *not yet recorded* |
| work disk, total (GB) | *not yet recorded* |
| work disk, free (GB) | *not yet recorded* |

## What to compare against your own run

- **vCPUs and RAM** should match the instance type you chose. If they do not, the space is running on a different instance type than the materials assume.
- **Available RAM** will be lower than total RAM, and lower still after you have loaded data. That is normal.
- **Work disk, total** should be close to the storage size on the space page, not the size of S3 and not your laptop's disk.
- **Computer name** should differ from the name your laptop prints in Positron. If they match, the notebook ran in the wrong place.
