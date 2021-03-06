from abc import ABC, abstractmethod

from torch.nn import Module


class PointwiseModel(Module, ABC):
    """
    Base Pointwise Model class
    """
    def __init__(self):
        super(PointwiseModel, self).__init__()

    @abstractmethod
    def forward(self, *input0):
        pass


class Classifier(ABC):
    """
    Base Classifier
    """

    @abstractmethod
    def _initialize(self, x, **kwargs):
        pass

    @abstractmethod
    def _init_dataset(self, x, **kwargs):
        pass

    @abstractmethod
    def _init_model(self, **kwargs):
        pass

    @abstractmethod
    def fit(self, x, y, **kwargs):
        pass

    @abstractmethod
    def predict(self, x, **kwargs):
        pass
