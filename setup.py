from setuptools import setup, find_packages

setup(
    name="mispm",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'numpy',
        'scipy',
        'pandas',
        'matplotlib',
        'nibabel',
        'PyQt5',
        'tqdm'
    ]
)
