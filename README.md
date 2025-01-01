# cython-template

This is a Cython multi-submodule template project.

## Instructions

Clone this repo, and run `pip install Cython setuptools pyparsing` in the cloned directory after creating a virtual environment to install
the development dependencies.

Run `python setup.py build_ext --inplace` to compile the extension module and generate the stub files.

> [!NOTE]
> The stub files are not perfect, and do not accurately translate all of Cython to Python's types. The goal is to provide a starting point for writing better stubs if typing information is a priority.

Run `python main.py` to run the test script.
