# AWS Sessions for GSB 5544

Course materials for the AWS-focused sessions of **GSB 5544 · Computing and Machine Learning for Business Analytics**.

**Website:** https://gato365.github.io/aws-gsb-5544-sessions/

The site is the best place to start. It shows the status of each session, what students will do, and links to every document as a rendered page and a downloadable notebook.

## What Session 1 teaches

Students use their own AWS account to process NOAA weather data on a remote SageMaker machine, download a compact summary, visualize it locally in Positron, and compare the resources and elapsed time of the two machines.

## Layout

```
session_1/
  01_preclass_reading.md                  concepts, laptop measurements, account setup
  02_topics_of_practice.ipynb             short in-class notebook, runs on SageMaker
  03_practice_activity_remote.ipynb       guided workflow, steps 1-6, runs on SageMaker
  03_practice_activity_local.ipynb        guided workflow, steps 7-8, runs in Positron
  04_lab_remote.ipynb                     inventory-planning lab, analyze and export, SageMaker
  04_lab_local.ipynb                      inventory-planning lab, visualize and interpret, Positron
  05_athena_extension_guide.md            optional: Athena
  05_athena_extension.ipynb               optional: Athena notebook, SageMaker
  06_extraction_strategies_optional.md    optional: longer extraction exercises and cost detail
  *_SOLUTIONS.ipynb                       instructor copy of each notebook
  build_notebooks.py                      generates all twelve notebooks from one source
  CHANGELOG.md                            what changed and what was tested
  images/                                 setup screenshots used by the reading
  lab/                                    optional challenge lab (function-writing) and its instructor files
_quarto.yml                               site configuration
index.qmd                                 site home page
docs/                                     rendered site (served by GitHub Pages)
```

## Rebuilding

Notebooks: edit `session_1/build_notebooks.py`, then

```bash
cd session_1 && python build_notebooks.py     # needs nbformat
```

Never edit the `.ipynb` files directly; the next build overwrites them.

The build also copies the solution notebooks into the instructor's course folder (`INSTRUCTOR_COPY` in `build_notebooks.py`).

Site: from the repository root

```bash
quarto render
```

Commit the regenerated `docs/` folder and push. GitHub Pages serves `docs/` on the `main` branch.

## Requirements for students

- Positron with a Python environment, and

```bash
pip install boto3 pandas pyarrow fsspec s3fs psutil matplotlib
```

- Their own AWS account on the Free plan, with SageMaker Studio set up as described in the pre-class reading. The NOAA data is public and is read anonymously; the account is needed to rent the remote computer, not to reach the data.
