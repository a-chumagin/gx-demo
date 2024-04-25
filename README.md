# Project Title

This project is based on the Jupyter notebook `gx-demo.ipynb`. It demonstrates the usage of the GX library for data testing

## Description

This project uses the GX library to perform various data analysis tasks. The `gx-demo.ipynb` notebook contains step-by-step instructions and code snippets for using the library. It covers topics such as data loading, preprocessing, visualization, and model training.

## Installation

This project requires Python and several Python libraries. The required libraries are listed in the `requirements.txt` file. You can install them using pip:

```bash
pip install -r requirements.txt
```



## Flow
```
- Set up GX context.
- Prepare data.
- Profile data (optional).
- Generate technical tests from profile.
- Add business tests.
- Create a checkpoint.
- Run the checkpoint on initial data.
- Load new data.
- Run the checkpoint on new data and build data docs.
```