# Add to import path:
# python setup.py develop

from setuptools import setup, find_packages

setup(
    name="pokeai",
    version="1.0",
    packages=find_packages(),
    test_suite='test',
    python_requires='>=3.8',
    install_requires=['numpy', 'torch', 'pymongo', 'optuna', 'tqdm']
)
