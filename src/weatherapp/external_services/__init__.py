import os
from pathlib import Path

from dotenv import dotenv_values


# def load_tests(loader, standard_tests, pattern):
#     pkg_dir = Path(__file__)
#     os.environ.update(dotenv_values(pkg_dir / '.env.test'))
#     package_tests = loader.discover(start_dir=str(pkg_dir), pattern=pattern)
#     standard_tests.addTests(package_tests)
#     return standard_tests
