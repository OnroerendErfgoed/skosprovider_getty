.. _development:

Development
===========

Skosprovider_getty is being developed by the 
`Flanders Heritage Agency`_.

Since we place a lot of importance on code quality, we expect to have a good 
amount of code coverage present and run frequent unit tests. All commits and
pull requests will be tested with `Travis-ci`_. Code coverage is being 
monitored with `Coveralls`_.

Locally you can run unit tests by using `pytest`_ or `tox`_. Running pytest 
manually is good for running a distinct set of unit tests. For a full test run, 
tox is preferred since this can run the unit tests against multiple versions of
python.

.. code-block:: bash

    # Setup for development
    $ python setup.py develop
    # Run unit tests for all environments 
    $ tox
    # No coverage
    $ py.test 
    # Coverage
    $ py.test --cov skosprovider_getty --cov-report term-missing tests
    # Only run a subset of the tests
    $ py.test skosprovider_getty/tests/test_providers.py


Please provide new unit tests to maintain 100% coverage. If you send us a pull request
and this build doesn't function, please correct the issue at hand or let us 
know why it's not working.

.. _Flanders Heritage Agency: https://www.onroerenderfgoed.be
.. _Travis-ci: https://travis-ci.org/OnroerendErfgoed/skosprovider_getty
.. _Coveralls: https://coveralls.io/r/OnroerendErfgoed/skosprovider_getty
.. _pytest: http://pytest.org
.. _tox: http://tox.readthedocs.org
