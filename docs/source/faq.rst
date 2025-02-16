FAQ
===

.. contents::
    :local:

Can I use Optuna with X? (where X is your favorite ML library)
--------------------------------------------------------------

Optuna is compatible with most ML libraries, and it's easy to use Optuna with those.
Please refer to `examples <https://github.com/optuna/optuna-examples/>`_.


.. _objective-func-additional-args:

How to define objective functions that have own arguments?
----------------------------------------------------------

There are two ways to realize it.

First, callable classes can be used for that purpose as follows:

.. code-block:: python

    import optuna


    class Objective(object):
        def __init__(self, min_x, max_x):
            # Hold this implementation specific arguments as the fields of the class.
            self.min_x = min_x
            self.max_x = max_x

        def __call__(self, trial):
            # Calculate an objective value by using the extra arguments.
            x = trial.suggest_float("x", self.min_x, self.max_x)
            return (x - 2) ** 2


    # Execute an optimization by using an `Objective` instance.
    study = optuna.create_study()
    study.optimize(Objective(-100, 100), n_trials=100)


Second, you can use ``lambda`` or ``functools.partial`` for creating functions (closures) that hold extra arguments.
Below is an example that uses ``lambda``:

.. code-block:: python

    import optuna

    # Objective function that takes three arguments.
    def objective(trial, min_x, max_x):
        x = trial.suggest_float("x", min_x, max_x)
        return (x - 2) ** 2


    # Extra arguments.
    min_x = -100
    max_x = 100

    # Execute an optimization by using the above objective function wrapped by `lambda`.
    study = optuna.create_study()
    study.optimize(lambda trial: objective(trial, min_x, max_x), n_trials=100)

Please also refer to `sklearn_addtitional_args.py <https://github.com/optuna/optuna-examples/tree/main/sklearn/sklearn_additional_args.py>`_ example,
which reuses the dataset instead of loading it in each trial execution.


Can I use Optuna without remote RDB servers?
--------------------------------------------

Yes, it's possible.

In the simplest form, Optuna works with in-memory storage:

.. code-block:: python

    study = optuna.create_study()
    study.optimize(objective)


If you want to save and resume studies,  it's handy to use SQLite as the local storage:

.. code-block:: python

    study = optuna.create_study(study_name="foo_study", storage="sqlite:///example.db")
    study.optimize(objective)  # The state of `study` will be persisted to the local SQLite file.

Please see :ref:`rdb` for more details.


How can I save and resume studies?
----------------------------------------------------

There are two ways of persisting studies, which depend if you are using
in-memory storage (default) or remote databases (RDB). In-memory studies can be
saved and loaded like usual Python objects using ``pickle`` or ``joblib``. For
example, using ``joblib``:

.. code-block:: python

    study = optuna.create_study()
    joblib.dump(study, "study.pkl")

And to resume the study:

.. code-block:: python

    study = joblib.load("study.pkl")
    print("Best trial until now:")
    print(" Value: ", study.best_trial.value)
    print(" Params: ")
    for key, value in study.best_trial.params.items():
        print(f"    {key}: {value}")

Note that Optuna does not support saving/reloading across different Optuna
versions with ``pickle``. To save/reload a study across different Optuna versions,
please use RDBs and `upgrade storage schema <reference/cli.html#storage-upgrade>`_
if necessary. If you are using RDBs, see :ref:`rdb` for more details.

How to suppress log messages of Optuna?
---------------------------------------

By default, Optuna shows log messages at the ``optuna.logging.INFO`` level.
You can change logging levels by using  :func:`optuna.logging.set_verbosity`.

For instance, you can stop showing each trial result as follows:

.. code-block:: python

    optuna.logging.set_verbosity(optuna.logging.WARNING)

    study = optuna.create_study()
    study.optimize(objective)
    # Logs like '[I 2020-07-21 13:41:45,627] Trial 0 finished with value:...' are disabled.


Please refer to :class:`optuna.logging` for further details.


How to save machine learning models trained in objective functions?
-------------------------------------------------------------------

Optuna saves hyperparameter values with its corresponding objective value to storage,
but it discards intermediate objects such as machine learning models and neural network weights.
To save models or weights, please use features of the machine learning library you used.

We recommend saving :obj:`optuna.trial.Trial.number` with a model in order to identify its corresponding trial.
For example, you can save SVM models trained in the objective function as follows:

.. code-block:: python

    def objective(trial):
        svc_c = trial.suggest_float("svc_c", 1e-10, 1e10, log=True)
        clf = sklearn.svm.SVC(C=svc_c)
        clf.fit(X_train, y_train)

        # Save a trained model to a file.
        with open("{}.pickle".format(trial.number), "wb") as fout:
            pickle.dump(clf, fout)
        return 1.0 - accuracy_score(y_valid, clf.predict(X_valid))


    study = optuna.create_study()
    study.optimize(objective, n_trials=100)

    # Load the best model.
    with open("{}.pickle".format(study.best_trial.number), "rb") as fin:
        best_clf = pickle.load(fin)
    print(accuracy_score(y_valid, best_clf.predict(X_valid)))


How can I obtain reproducible optimization results?
---------------------------------------------------

To make the parameters suggested by Optuna reproducible, you can specify a fixed random seed via ``seed`` argument of :class:`~optuna.samplers.RandomSampler` or :class:`~optuna.samplers.TPESampler` as follows:

.. code-block:: python

    sampler = TPESampler(seed=10)  # Make the sampler behave in a deterministic way.
    study = optuna.create_study(sampler=sampler)
    study.optimize(objective)

However, there are two caveats.

First, when optimizing a study in distributed or parallel mode, there is inherent non-determinism.
Thus it is very difficult to reproduce the same results in such condition.
We recommend executing optimization of a study sequentially if you would like to reproduce the result.

Second, if your objective function behaves in a non-deterministic way (i.e., it does not return the same value even if the same parameters were suggested), you cannot reproduce an optimization.
To deal with this problem, please set an option (e.g., random seed) to make the behavior deterministic if your optimization target (e.g., an ML library) provides it.


How are exceptions from trials handled?
---------------------------------------

Trials that raise exceptions without catching them will be treated as failures, i.e. with the :obj:`~optuna.trial.TrialState.FAIL` status.

By default, all exceptions except :class:`~optuna.exceptions.TrialPruned` raised in objective functions are propagated to the caller of :func:`~optuna.study.Study.optimize`.
In other words, studies are aborted when such exceptions are raised.
It might be desirable to continue a study with the remaining trials.
To do so, you can specify in :func:`~optuna.study.Study.optimize` which exception types to catch using the ``catch`` argument.
Exceptions of these types are caught inside the study and will not propagate further.

You can find the failed trials in log messages.

.. code-block:: sh

    [W 2018-12-07 16:38:36,889] Setting status of trial#0 as TrialState.FAIL because of \
    the following error: ValueError('A sample error in objective.')

You can also find the failed trials by checking the trial states as follows:

.. code-block:: python

    study.trials_dataframe()

.. csv-table::

    number,state,value,...,params,system_attrs
    0,TrialState.FAIL,,...,0,Setting status of trial#0 as TrialState.FAIL because of the following error: ValueError('A test error in objective.')
    1,TrialState.COMPLETE,1269,...,1,

.. seealso::

    The ``catch`` argument in :func:`~optuna.study.Study.optimize`.


How are NaNs returned by trials handled?
----------------------------------------

Trials that return :obj:`NaN` (``float('nan')``) are treated as failures, but they will not abort studies.

Trials which return :obj:`NaN` are shown as follows:

.. code-block:: sh

    [W 2018-12-07 16:41:59,000] Setting status of trial#2 as TrialState.FAIL because the \
    objective function returned nan.


What happens when I dynamically alter a search space?
-----------------------------------------------------

Since parameters search spaces are specified in each call to the suggestion API, e.g.
:func:`~optuna.trial.Trial.suggest_float` and :func:`~optuna.trial.Trial.suggest_int`,
it is possible to, in a single study, alter the range by sampling parameters from different search
spaces in different trials.
The behavior when altered is defined by each sampler individually.

.. note::

    Discussion about the TPE sampler. https://github.com/optuna/optuna/issues/822


How can I use two GPUs for evaluating two trials simultaneously?
----------------------------------------------------------------

If your optimization target supports GPU (CUDA) acceleration and you want to specify which GPU is used, the easiest way is to set ``CUDA_VISIBLE_DEVICES`` environment variable:

.. code-block:: bash

    # On a terminal.
    #
    # Specify to use the first GPU, and run an optimization.
    $ export CUDA_VISIBLE_DEVICES=0
    $ optuna study optimize foo.py objective --study-name foo --storage sqlite:///example.db

    # On another terminal.
    #
    # Specify to use the second GPU, and run another optimization.
    $ export CUDA_VISIBLE_DEVICES=1
    $ optuna study optimize bar.py objective --study-name bar --storage sqlite:///example.db

Please refer to `CUDA C Programming Guide <https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html#env-vars>`_ for further details.


How can I test my objective functions?
--------------------------------------

When you test objective functions, you may prefer fixed parameter values to sampled ones.
In that case, you can use :class:`~optuna.trial.FixedTrial`, which suggests fixed parameter values based on a given dictionary of parameters.
For instance, you can input arbitrary values of :math:`x` and :math:`y` to the objective function :math:`x + y` as follows:

.. code-block:: python

    def objective(trial):
        x = trial.suggest_float("x", -1.0, 1.0)
        y = trial.suggest_int("y", -5, 5)
        return x + y


    objective(FixedTrial({"x": 1.0, "y": -1}))  # 0.0
    objective(FixedTrial({"x": -1.0, "y": -4}))  # -5.0


Using :class:`~optuna.trial.FixedTrial`, you can write unit tests as follows:

.. code-block:: python

    # A test function of pytest
    def test_objective():
        assert 1.0 == objective(FixedTrial({"x": 1.0, "y": 0}))
        assert -1.0 == objective(FixedTrial({"x": 0.0, "y": -1}))
        assert 0.0 == objective(FixedTrial({"x": -1.0, "y": 1}))


.. _out-of-memory-gc-collect:

How do I avoid running out of memory (OOM) when optimizing studies?
-------------------------------------------------------------------

If the memory footprint increases as you run more trials, try to periodically run the garbage collector.
Specify ``gc_after_trial`` to :obj:`True` when calling :func:`~optuna.study.Study.optimize` or call :func:`gc.collect` inside a callback.

.. code-block:: python

    def objective(trial):
        x = trial.suggest_float("x", -1.0, 1.0)
        y = trial.suggest_int("y", -5, 5)
        return x + y


    study = optuna.create_study()
    study.optimize(objective, n_trials=10, gc_after_trial=True)

    # `gc_after_trial=True` is more or less identical to the following.
    study.optimize(objective, n_trials=10, callbacks=[lambda study, trial: gc.collect()])

There is a performance trade-off for running the garbage collector, which could be non-negligible depending on how fast your objective function otherwise is. Therefore, ``gc_after_trial`` is :obj:`False` by default.
Note that the above examples are similar to running the garbage collector inside the objective function, except for the fact that :func:`gc.collect` is called even when errors, including :class:`~optuna.exceptions.TrialPruned` are raised.

.. note::

    :class:`~optuna.integration.ChainerMNStudy` does currently not provide ``gc_after_trial`` nor callbacks for :func:`~optuna.integration.ChainerMNStudy.optimize`.
    When using this class, you will have to call the garbage collector inside the objective function.

How can I output a log only when the best value is updated?
-----------------------------------------------------------

Here's how to replace the logging feature of optuna with your own logging callback function.
The implemented callback can be passed to :func:`~optuna.study.Study.optimize`.
Here's an example:

.. code-block:: python

    import optuna


    # Turn off optuna log notes.
    optuna.logging.set_verbosity(optuna.logging.WARN)


    def objective(trial):
        x = trial.suggest_float("x", 0, 1)
        return x ** 2


    def logging_callback(study, frozen_trial):
        previous_best_value = study.user_attrs.get("previous_best_value", None)
        if previous_best_value != study.best_value:
            study.set_user_attr("previous_best_value", study.best_value)
            print(
                "Trial {} finished with best value: {} and parameters: {}. ".format(
                frozen_trial.number,
                frozen_trial.value,
                frozen_trial.params,
                )
            )


    study = optuna.create_study()
    study.optimize(objective, n_trials=100, callbacks=[logging_callback])

How do I suggest variables which represent the proportion, that is, are in accordance with Dirichlet distribution?
------------------------------------------------------------------------------------------------------------------

When you want to suggest :math:`n` variables which represent the proportion, that is, :math:`p[0], p[1], ..., p[n-1]` which satisfy :math:`0 \le p[k] \le 1` for any :math:`k` and :math:`p[0] + p[1] + ... + p[n-1] = 1`, try the below.
For example, these variables can be used as weights when interpolating the loss functions.
These variables are in accordance with the flat `Dirichlet distribution <https://en.wikipedia.org/wiki/Dirichlet_distribution>`_.

.. code-block:: python

    import numpy as np
    import matplotlib.pyplot as plt
    import optuna


    def objective(trial):
        n = 5
        x = []
        for i in range(n):
            x.append(- np.log(trial.suggest_float(f"x_{i}", 0, 1)))

        p = []
        for i in range(n):
            p.append(x[i] / sum(x))

        for i in range(n):
            trial.set_user_attr(f"p_{i}", p[i])

        return 0

    study = optuna.create_study(sampler=optuna.samplers.RandomSampler())
    study.optimize(objective, n_trials=1000)

    n = 5
    p = []
    for i in range(n):
        p.append([trial.user_attrs[f"p_{i}"] for trial in study.trials])
    axes = plt.subplots(n, n, figsize=(20, 20))[1]

    for i in range(n):
        for j in range(n):
            axes[j][i].scatter(p[i], p[j], marker=".")
            axes[j][i].set_xlim(0, 1)
            axes[j][i].set_ylim(0, 1)
            axes[j][i].set_xlabel(f"p_{i}")
            axes[j][i].set_ylabel(f"p_{j}")

    plt.savefig("sampled_ps.png")

This method is justified in the following way:
First, if we apply the transformation :math:`x = - \log (u)` to the variable :math:`u` sampled from the uniform distribution :math:`Uni(0, 1)` in the interval :math:`[0, 1]`, the variable :math:`x` will follow the exponential distribution :math:`Exp(1)` with scale parameter :math:`1`.
Furthermore, for :math:`n` variables :math:`x[0], ..., x[n-1]` that follow the exponential distribution of scale parameter :math:`1` independently, normalizing them with :math:`p[i] = x[i] / \sum_i x[i]`, the vector :math:`p` follows the Dirichlet distribution :math:`Dir(\alpha)` of scale parameter :math:`\alpha = (1, ..., 1)`.
You can verify the transformation by calculating the elements of the Jacobian.
