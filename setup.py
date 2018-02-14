#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from typing import List

from setuptools import setup
from pip.req import parse_requirements

if sys.version_info < (3, 6):
    sys.exit('Only Python 3.6+ is supported.')


def get_version(string: str) -> str:
    """
    Get a version string from a string with a ``__version__`` attribute.

    Args:
        string: The string to search for a version substring.

    Returns:
        The parsed version string.

    Raises:
        RuntimeError: If a version string could not be matched.
    """
    flags = re.S
    pattern = r".*__version__ = '(.*?)'"
    match = re.match(pattern=pattern, string=string, flags=flags)

    if match:
        return match.group(1)

    raise RuntimeError('No version string could be matched')


def get_reqs(path: Path) -> List[str]:
    """
    Get a list of pip-compatible version strings.

    Args:
        path: The path to a requirements file.

    Returns:
        The pip-compatible version strings.
    """
    return [str(r.req) for r in parse_requirements(str(path), session=False)]

here = Path(__name__).cwd()
readme = (here / 'README.rst').read_text()
version = get_version((here / 'layabout.py').read_text())
install_reqs = get_reqs(here / 'requirements.txt')
test_reqs = get_reqs(here / 'test-requirements.txt')
dev_reqs = get_reqs(here / 'dev-requirements.txt')

setup(
    name='layabout',
    version=version,
    description='A small event handling library on top of the Slack RTM API. ',
    long_description=readme,
    author='Reilly Tucker Siemens',
    author_email='reilly@tuckersiemens.com',
    url='https://github.com/reillysiemens/wb2k',
    install_requires=install_reqs,
    license='ISCL',
    zip_safe=False,
    py_modules=['layabout'],
    keywords='Slack RTM API',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Operating System :: POSIX :: BSD :: FreeBSD',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Communications :: Chat',
        'Topic :: Software Development :: Libraries',
    ],
    test_suite='tests',
    tests_require=test_reqs,
    extras_require={
        'dev': dev_reqs,
        'test': test_reqs,
    },
)
