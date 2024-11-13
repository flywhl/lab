from pathlib import Path
import pytest
from uuid import uuid4

from lab.model.project import Experiment, Project, ValueReference
from lab.service.experiment import ExperimentService
from lab.service.pipeline import PipelineService


@pytest.fixture
def experiment_service():
    return ExperimentService()


@pytest.fixture
def pipeline_service(experiment_service):
    return PipelineService(experiment_service=experiment_service)


def test_orders_independent_experiments(pipeline_service):
    """Test that independent experiments remain in original order"""
    exp1 = Experiment(id=uuid4(), name="exp1", path=Path("exp1.py"), parameters={})
    exp2 = Experiment(id=uuid4(), name="exp2", path=Path("exp2.py"), parameters={})
    
    project = Project(experiments=[exp1, exp2])
    pipeline = pipeline_service.create_pipeline(project)
    
    assert pipeline.experiments == [exp1, exp2]


def test_orders_dependent_experiments(pipeline_service):
    """Test that dependent experiments are ordered correctly"""
    exp1 = Experiment(id=uuid4(), name="exp1", path=Path("exp1.py"), parameters={})
    exp2 = Experiment(
        id=uuid4(),
        name="exp2",
        path=Path("exp2.py"),
        parameters={"input": ValueReference(owner=exp1, attribute="exp1.output")},
    )
    
    # Even if exp2 comes first in project, it should be ordered after exp1
    project = Project(experiments=[exp2, exp1])
    pipeline = pipeline_service.create_pipeline(project)
    
    assert pipeline.experiments == [exp1, exp2]


def test_orders_chain_of_dependencies(pipeline_service):
    """Test that a chain of dependencies is ordered correctly"""
    exp1 = Experiment(id=uuid4(), name="exp1", path=Path("exp1.py"), parameters={})
    exp2 = Experiment(
        id=uuid4(),
        name="exp2",
        path=Path("exp2.py"),
        parameters={"input": ValueReference(owner=exp1, attribute="exp1.output")},
    )
    exp3 = Experiment(
        id=uuid4(),
        name="exp3",
        path=Path("exp3.py"),
        parameters={"input": ValueReference(owner=exp2, attribute="exp2.output")},
    )
    
    # Even if experiments are in random order in project
    project = Project(experiments=[exp2, exp3, exp1])
    pipeline = pipeline_service.create_pipeline(project)
    
    assert pipeline.experiments == [exp1, exp2, exp3]


def test_detects_circular_dependencies(pipeline_service):
    """Test that circular dependencies raise ValueError"""
    exp1 = Experiment(id=uuid4(), name="exp1", path=Path("exp1.py"), parameters={})
    exp2 = Experiment(
        id=uuid4(),
        name="exp2",
        path=Path("exp2.py"),
        parameters={"input": ValueReference(owner=exp1, attribute="exp1.output")},
    )
    # Create circular dependency by making exp1 depend on exp2
    exp1.parameters["input"] = ValueReference(owner=exp2, attribute="exp2.output")
    
    project = Project(experiments=[exp1, exp2])
    
    with pytest.raises(ValueError, match="Circular dependency detected"):
        pipeline_service.create_pipeline(project)
