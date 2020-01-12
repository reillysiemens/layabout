#!/usr/bin/env python3
import re
import sys

from setuptools import setup

if sys.version_info < (3, 6):
    sys.exit('Layabout only supports Python 3.6+.')

from pathlib import Path  # noqa: pathlib can't be imported in Python < 3.4.


def get_version(string):
    """ Retrieve the ``__version__`` attribute for Layabout. """
    flags = re.S
    pattern = r".*__version__ = '(.*?)'"
    match = re.match(pattern=pattern, string=string, flags=flags)

    if match:
        return match.group(1)

    raise RuntimeError('No version string could be matched')


here = Path(__name__).cwd()
readme = (here / 'README.rst').read_text()
version = get_version((here / 'layabout.py').read_text())

# Requirements.
install_reqs = [
    'slackclient~=1.2',
]
test_reqs = [
    'flake8~=3.7.8',
    'mypy~=0.740.0',
    'pytest~=5.2',
    'pytest-cov~=2.8',
]
docs_reqs = [
    'Sphinx~=2.2',
    'sphinx-autodoc-typehints~=1.8',
]
dev_reqs = test_reqs + docs_reqs

setup(
    name='layabout',
    version=version,
    description='A small event handling library on top of the Slack RTM API.',
    long_description=readme,
    author='Reilly Tucker Siemens',
    author_email='reilly@tuckersiemens.com',
    url='https://github.com/reillysiemens/layabout',
    install_requires=install_reqs,
    license='ISCL',
    py_modules=['layabout'],
    keywords='Slack RTM API Bot Framework',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Operating System :: POSIX :: BSD :: FreeBSD',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Communications :: Chat',
        'Topic :: Software Development :: Libraries',
    ],
    test_suite='tests',
    tests_require=test_reqs,
    python_requires='>=3.6',
    extras_require={
        'dev': dev_reqs,
        'docs': docs_reqs,
        'test': test_reqs,
    },
)
