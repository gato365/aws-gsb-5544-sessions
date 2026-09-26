# AWS Sessions for GSB 5544

Course materials for the AWS-focused sessions of **GSB 5544 · Computing and Machine Learning for Business Analytics**.

**Website:** https://gato365.github.io/aws-gsb-5544-sessions/

The site is the best place to start. It shows the status of each session, what students will do, and links to every document as a rendered page, a downloadable notebook, and a Google Colab link.

## Layout

```
session_1/
  01_preclass_reading.md                 read before class
  02_topics_of_practice.ipynb            in-class fill-in-the-blank (student)
  02_topics_of_practice_SOLUTIONS.ipynb  instructor copy
  03_practice_activity.ipynb             scenario with 11 questions (student)
  03_practice_activity_SOLUTIONS.ipynb   instructor copy
  build_notebooks.py                     generates all four notebooks from one source
_quarto.yml                              site configuration
index.qmd                                site home page
docs/                                    rendered site (served by GitHub Pages)
```

## Rebuilding

Notebooks: edit `session_1/build_notebooks.py`, then

```bash
cd session_1 && python build_notebooks.py
```

Site: from the repository root

```bash
quarto render
```

Commit the regenerated `docs/` folder and push. GitHub Pages serves `docs/` on the `main` branch.

## Requirements for students

```bash
pip install psutil boto3 pandas matplotlib
```

No AWS account is needed. All data is read anonymously from the public `noaa-ghcn-pds` bucket.
