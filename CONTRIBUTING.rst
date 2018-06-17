Contributing Guidelines
=======================

Please follow these guidelines for contributing to this project.

Repository Management
---------------------

- Fork this project into your own repository.
- Follow the `version control`_ guidelines.
- No changes should reach the ``master`` branch except by way of a
  `pull request`_.

Submitting Issues
~~~~~~~~~~~~~~~~~

Create an issue to report bugs or request enhancements. Better yet, fix the
problem yourself and submit a `pull request`_.

Bug Reports
+++++++++++

When reporting a bug, please provide the steps to reproduce the problem and any
details that could be important such as whether this is the first time this has
happened or whether others are experiencing it.

Pull Requests
+++++++++++++

PRs must remain focused on fixing or addressing one thing (see `topic branch`_
model). Make sure your pull request contains a clear title and description.
Test coverage should not drop as a result. If you add code, you add tests.

Be sure to follow the guidelines on `writing code`_ if you want your work
considered for inclusion.

Handling Pull Requests
~~~~~~~~~~~~~~~~~~~~~~

- Pull Requests **must** include:

  - Title describing the change
  - Description explaining the change in detail
  - Tests

- A maintainer will respond to Pull Requests with one of:

  - 'Ship It', 'LGTM', 🚢, or some other affirmation
  - What must be changed
  - Won't accept and why

Nota Bene
+++++++++

- PRs which have titles beginning with ``[WIP]`` (indicating a Work In
  Progress) status will **not** be merged until the ``[WIP]`` prefix has been
  removed from the title. This is a good way to get feedback from maintainers
  if you are unsure of the changes you are making.
- A PR that has received a 'Ship It' may not be merged immediately.
- You may be asked to rebase or squash your commits to keep an orderly version
  control history.

.. _writing code:

Writing Code
------------

Writing code is a creative process and there will always be exceptions to the
rules, but it's good to maintain certain standards. In general, please follow
these code conventions.

Coding Style
~~~~~~~~~~~~

- Follow :pep:`8` guidelines.
- Code in this project **must** be linted. For convenience the project Makefile
  contains a ``lint`` target to run the linting process for you.
- Try to respect the style of existing code.

.. _version control:

Version Control
~~~~~~~~~~~~~~~

- `Fork`_ the `central repository`_ and work from a clone of your own fork.
- Follow the `topic branch`_ model and submit pull requests from branches named
  according to their purpose.
- Review the `GitHub Flow`_ documentation and, in general, try to stick to the
  principles outlined there.

Testing
~~~~~~~
- Code **must** be tested. Write or update related unit tests so you don't have
  to manually retest the same thing many times.
- Tests for this project are written using the `pytest`_ framework. While it
  isn't always achievable this project strives to maintain 100% test coverage.
  For convenience the project Makefile contains a ``test`` target to run the
  tests and generate coverage for you.
- In addition to unit testing code in this project is statically type checked
  using `mypy`_. For convenience the project Makefile contains a ``type-check``
  target to run mypy for you.

Documentation
~~~~~~~~~~~~~
- Public interfaces **must** be thoroughly documented. At a minimum this
  includes inputs, return types, exceptions raised, and surprising behavior
  like state changes.
- Documentation for this project is written in `reStructuredText`_ and
  generated with `Sphinx`_. For convenience the project Makefile contains a
  ``docs`` to run Sphinx for you.


.. _pull request: https://help.github.com/articles/using-pull-requests/
.. _topic branch: https://git-scm.com/book/en/v2/Git-Branching-Branching-Workflows#Topic-Branches
.. _Fork: https://help.github.com/articles/fork-a-repo/
.. _central repository: https://github.com/reillysiemens/layabout/
.. _GitHub Flow: https://guides.github.com/introduction/flow/
.. _pytest: https://docs.pytest.org/en/latest/
.. _mypy: http://www.mypy-lang.org/
.. _reStructuredText: http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
.. _Sphinx: http://www.sphinx-doc.org/en/master/index.html
