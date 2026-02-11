"""Setup script for MLOps package"""

from setuptools import setup, find_packages

setup(
    name="databricks-mlops",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "mlflow>=2.10.0",
        "scikit-learn>=1.3.2",
        "pandas>=2.1.4",
        "numpy>=1.26.2",
    ],
    python_requires=">=3.10",
)
