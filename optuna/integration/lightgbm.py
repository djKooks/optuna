from __future__ import absolute_import

import optuna

try:
    import lightgbm as lgb  # NOQA
    _available = True
except ImportError as e:
    _import_error = e
    # LightGBMPruningCallback is disabled because LightGBM is not available.
    _available = False


class LightGBMPruningCallback(object):
    """Callback for LightGBM to prune unpromising trials.

    Example:

        Add a pruning callback which observes validation scores to training of a LightGBM model.

        .. code::

                param = {'objective': 'binary', 'metric': 'binary_error'}
                pruning_callback = LightGBMPruningCallback(trial, 'binary_error')
                gbm = lgb.train(param, dtrain, num_round, valid_sets=[dtest],
                                callbacks=[pruning_callback])

    Args:
        trial:
            A :class:`~optuna.trial.Trial` corresponding to the current evaluation of
            the objective function.
        metric:
            An evaluation metric for pruning, e.g., ``binary_error`` and ``multi_error``.
            Please refer to
            `LightGBM reference
            <https://lightgbm.readthedocs.io/en/latest/Parameters.html#metric>`_
            for further details.
        valid_name:
            The name of the target validation.
            Validation names are specified by ``valid_names`` option of
            `train method
            <https://lightgbm.readthedocs.io/en/latest/Python-API.html#lightgbm.train>`_.
            If omitted, ``valid_0`` is used which is the default name of the first validation.
    """

    def __init__(self, trial, metric, valid_name='valid_0'):
        # type: (optuna.trial.Trial, str, str) -> None

        _check_lightgbm_availability()

        self.trial = trial
        self.valid_name = valid_name
        self.metric = metric

    def __call__(self, env):
        # type: (lgb.callback.CallbackEnv) -> None

        for valid_name, metric, current_score, is_higher_better in env.evaluation_result_list:
            if valid_name != self.valid_name or metric != self.metric:
                continue

            # TODO(ohta): Deal with maximize direction
            if is_higher_better:
                raise ValueError(
                    'Pruning using metrics to be maximized has not been supported yet '
                    '(validation_name: {}, metric: {}).'.format(valid_name, metric))

            self.trial.report(current_score, step=env.iteration)
            if self.trial.should_prune(env.iteration):
                message = "Trial was pruned at iteration {}.".format(env.iteration)
                raise optuna.structs.TrialPruned(message)
            return None

        raise ValueError(
            'The entry associated with the validation name "{}" and the metric name "{}" '
            'is not found in the evaluation result list {}.'.format(
                self.valid_name, self.metric, str(env.evaluation_result_list)))


def _check_lightgbm_availability():
    # type: () -> None

    if not _available:
        raise ImportError(
            'LightGBM is not available. Please install LightGBM to use this feature. '
            'LightGBM can be installed by executing `$ pip install lightgbm`. '
            'For further information, please refer to the installation guide of LightGBM. '
            '(The actual import error is as follows: ' + str(_import_error) + ')')
