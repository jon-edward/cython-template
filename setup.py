import logging
from pathlib import Path
from setuptools import find_packages, setup, Extension

from Cython.Build import cythonize
from _cython_peg import cython_string_2_stub

src_dir = Path(__file__).parent.joinpath("cython_template")

cython_files = list(src_dir.rglob("*.pyx"))


def path_as_module_name(script_path: Path) -> str:
    """
    Convert a path to a module name
    """
    return script_path.relative_to(src_dir.parent).with_suffix("").as_posix().replace("/", ".")


extensions = [
    Extension(
        name=path_as_module_name(f),
        sources=[str(f)],
    )
    for f in cython_files
]


# generate stub files
for f in cython_files:
    input_text = f.read_text()
    stub, unparsed = cython_string_2_stub(input_text)

    if unparsed:
        logging.warning(f"Unparsed input in {f}, starting at character {len(input_text)-len(unparsed)}")
    
    with open(f.with_suffix(".pyi"), mode="w") as fi:
        fi.write(stub)


setup(
    name="cython_template",
    ext_modules=cythonize(extensions, language_level="3"),
    packages=find_packages(),
)
