import pytest

from optuna.importance import MeanDecreaseImpurityImportanceEvaluator
from optuna.study import create_study
from optuna.testing.visualization import prepare_study_with_trials
from optuna.trial import Trial
from optuna.visualization.matplotlib import plot_param_importances


def test_target_is_none_and_study_is_multi_obj() -> None:

    study = create_study(directions=["minimize", "minimize"])
    with pytest.raises(ValueError):
        plot_param_importances(study)


def test_plot_param_importances() -> None:

    # Test with no trial.
    study = create_study()
    figure = plot_param_importances(study)
    assert len(figure.get_lines()) == 0

    study = prepare_study_with_trials(with_c_d=True)

    # Test with a trial.
    figure = plot_param_importances(study)
    assert len(figure.get_lines()) == 0
    assert figure.xaxis.label.get_text() == "Importance for Objective Value"

    # Test with an evaluator.
    plot_param_importances(study, evaluator=MeanDecreaseImpurityImportanceEvaluator())
    assert len(figure.get_lines()) == 0
    assert figure.xaxis.label.get_text() == "Importance for Objective Value"

    # Test with a trial to select parameter.
    figure = plot_param_importances(study, params=["param_b"])
    assert len(figure.get_lines()) == 0
    assert figure.xaxis.label.get_text() == "Importance for Objective Value"

    # Test with a customized target value.
    with pytest.warns(UserWarning):
        figure = plot_param_importances(
            study, target=lambda t: t.params["param_b"] + t.params["param_d"]
        )
    assert len(figure.get_lines()) == 0

    # Test with a customized target name.
    figure = plot_param_importances(study, target_name="Target Name")
    assert len(figure.get_lines()) == 0
    assert figure.xaxis.label.get_text() == "Importance for Target Name"

    # Test with wrong parameters.
    with pytest.raises(ValueError):
        plot_param_importances(study, params=["optuna"])

    # Ignore failed trials.
    def fail_objective(_: Trial) -> float:

        raise ValueError

    study = create_study()
    study.optimize(fail_objective, n_trials=1, catch=(ValueError,))
    figure = plot_param_importances(study)
    assert len(figure.get_lines()) == 0
