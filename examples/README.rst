Examples of How to Use Layabout
===============================

This directory contains a bunch of examples showcasing various features of
Layabout. Getting started with all of them is roughly the same process.

Before going further, make sure you have `Pipenv`_ installed.

Install!
--------

In the directory of the example you want to try out, run:

.. code-block:: bash

   pipenv install

Thats it!

Run!
----

Now you can run the example with:

.. code-block:: bash

   pipenv run python example.py

Explore
=======

Getting started developing a slack integration can be overwhelming. We
recommend running the `simple`_ example first. It prints all events that your
app receives to the console, so it's a great way to interactively explore what
kind of events are available for you to handle.

A Brief Overview of Each Example
--------------------------------

- `simple`_: Registers a single catch-all event handler and prints it to
  ``stdout``.

.. _Pipenv: https://docs.pipenv.org/#install-pipenv-today
.. _simple: simple
