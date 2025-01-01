from uuid import UUID, uuid4
import pytest

from lab.project.model.project import Experiment, Project, ValueReference
from lab.project.model.plan import ExecutionPlan
from lab.project.service.plan import PlanService
from lab.runtime.model.execution import ScriptExecution


@pytest.fixture
def plan_service():
    return PlanService()


def create_experiment(name: str) -> Experiment:
    """Create a test experiment with the given name"""
    return Experiment(
        id=uuid4(),
        name=name,
        execution_method=ScriptExecution(command="echo", args=["test"]),
        parameters={},
    )


def test_creates_plan_for_empty_project(plan_service: PlanService) -> None:
    """Should handle empty projects gracefully"""
    project = Project(experiments=set())

    plan = plan_service.create_execution_plan(project)

    assert isinstance(plan, ExecutionPlan)
    assert plan.project == project
    assert len(plan.ordered_experiments) == 0


def test_creates_plan_for_independent_experiments(plan_service: PlanService) -> None:
    """Should preserve experiments when there are no dependencies"""
    exp1 = create_experiment("exp1")
    exp2 = create_experiment("exp2")
    project = Project(experiments={exp1, exp2})

    plan = plan_service.create_execution_plan(project)

    assert set(plan.ordered_experiments) == {exp1, exp2}


def test_orders_dependent_experiments(plan_service: PlanService) -> None:
    """Should order experiments based on dependencies"""
    exp1 = create_experiment("exp1")
    exp2 = create_experiment("exp2")
    exp2.parameters["input"] = ValueReference(owner=exp1, attribute="output")
    project = Project(experiments={exp1, exp2})

    plan = plan_service.create_execution_plan(project)

    assert plan.ordered_experiments == [exp1, exp2]


def test_detects_dependency_cycles(plan_service: PlanService) -> None:
    """Should raise ValueError when dependencies form a cycle"""
    exp1 = create_experiment("exp1")
    exp2 = create_experiment("exp2")
    exp1.parameters["input1"] = ValueReference(owner=exp2, attribute="output")
    exp2.parameters["input2"] = ValueReference(owner=exp1, attribute="output")
    project = Project(experiments={exp1, exp2})

    with pytest.raises(ValueError, match="contain cycles"):
        plan_service.create_execution_plan(project)


def test_handles_complex_dependencies(plan_service: PlanService) -> None:
    """Should correctly order experiments with complex dependencies"""
    exp1 = create_experiment("exp1")
    exp2 = create_experiment("exp2")
    exp3 = create_experiment("exp3")
    exp4 = create_experiment("exp4")

    # exp2 depends on exp1
    exp2.parameters["input"] = ValueReference(owner=exp1, attribute="output")
    # exp3 depends on exp1
    exp3.parameters["input"] = ValueReference(owner=exp1, attribute="output")
    # exp4 depends on exp2 and exp3
    exp4.parameters["input1"] = ValueReference(owner=exp2, attribute="output")
    exp4.parameters["input2"] = ValueReference(owner=exp3, attribute="output")

    project = Project(experiments={exp1, exp2, exp3, exp4})

    plan = plan_service.create_execution_plan(project)

    # exp1 must come first, exp4 must come last
    assert plan.ordered_experiments[0] == exp1
    assert plan.ordered_experiments[-1] == exp4
    # exp2 and exp3 can be in either order
    assert set(plan.ordered_experiments[1:3]) == {exp2, exp3}
