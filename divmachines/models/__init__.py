from __future__ import print_function
from torch import FloatTensor
import torch
from torch.nn import Module, Parameter
from divmachines.classifiers import PointwiseModel
from divmachines.models.layers import ScaledEmbedding, ZeroEmbedding


class MatrixFactorizationModel(PointwiseModel):
    """
    Matrix Factorization Model with Bias Parameters
    Parameters
    ----------
    n_users: int
        Number of users to use in user latent factors
    n_items: int
        Number of items to use in item latent factors
    n_factors: int, optional
        Number of factors to use in user and item latent factors
    sparse: boolean, optional
        Use sparse gradients for embedding layers.
    """
    def __init__(self,
                 n_users,
                 n_items,
                 n_factors=10,
                 sparse=True):

        super(MatrixFactorizationModel, self).__init__()
        self._n_users = n_users
        self._n_items = n_items
        self._n_factors = n_factors
        self._sparse = sparse

        self.x = ScaledEmbedding(self._n_users,
                                 self._n_factors,
                                 sparse=self._sparse)
        self.y = ScaledEmbedding(self._n_items,
                                 self._n_factors,
                                 sparse=self._sparse)

        self.user_biases = ZeroEmbedding(self._n_users, 1, sparse=self._sparse)
        self.item_biases = ZeroEmbedding(self._n_items, 1, sparse=self._sparse)

    def forward(self, user_ids, item_ids):
        """
        Compute the forward pass of the representation.
        Parameters
        ----------
        user_ids: tensor
            Tensor of user indices.
        item_ids: tensor
            Tensor of item indices.
        Returns
        -------
        predictions: tensor
            Tensor of predictions.
        """

        user_bias = self.user_biases(user_ids).squeeze()
        item_bias = self.item_biases(item_ids).squeeze()

        biases_sum = user_bias + item_bias

        users_batch = self.x(user_ids).squeeze()
        items_batch = self.y(item_ids).squeeze()

        if len(users_batch.size()) > 2:
            dot = (users_batch * items_batch).sum(2)
        elif len(users_batch.size()) > 1:
            dot = (users_batch * items_batch).sum(1)
        else:
            dot = (users_batch * items_batch).sum()

        return biases_sum + dot


class SimpleMatrixFactorizationModel(PointwiseModel):
    """
    Matrix Factorization Model without Bias Parameters
    Parameters
    ----------
    n_users: int
        Number of users to use in user latent factors
    n_items: int
        Number of items to use in item latent factors
    n_factors: int, optional
        Number of factors to use in user and item latent factors
    sparse: boolean, optional
        Use sparse gradients for embedding layers.
    """

    def __init__(self,
                 n_users,
                 n_items,
                 n_factors=10,
                 sparse=True):

        super(SimpleMatrixFactorizationModel, self).__init__()
        self._n_users = n_users
        self._n_items = n_items
        self._n_factors = n_factors
        self._sparse = sparse

        self.x = ScaledEmbedding(self._n_users,
                                 self._n_factors,
                                 sparse=self._sparse)
        self.y = ScaledEmbedding(self._n_items,
                                 self._n_factors,
                                 sparse=self._sparse)

    def forward(self, user_ids, item_ids):
        """
        Compute the forward pass of the representation.
        Parameters
        ----------
        user_ids: tensor
            Tensor of user indices.
        item_ids: tensor
            Tensor of item indices.
        Returns
        -------
        predictions: tensor
            Tensor of predictions.
        """

        users_batch = self.x(user_ids).squeeze()
        items_batch = self.y(item_ids).squeeze()

        if len(users_batch.size()) > 2:
            dot = (users_batch * items_batch).sum(2)
        elif len(users_batch.size()) > 1:
            dot = (users_batch * items_batch).sum(1)
        else:
            dot = (users_batch * items_batch).sum()

        return dot


class FactorizationMachine(PointwiseModel):
    """
    Pointwise Factorization Machine Model

    Parameters
    ----------
    n_features: int
        Length of the input vector.
    n_factors: int, optional
        Number of factors of the factorized parameters
    """
    def __init__(self, n_features, n_factors=10):

        super(FactorizationMachine, self).__init__()

        self.n_features, self.factors = n_features, n_factors
        self.linear = Parameter(FloatTensor(self.n_features))
        self.linear.data.uniform_(-0.01, 0.01)
        self.second_order = SecondOrderInteraction(self.n_features,
                                                   self.factors)

    def forward(self, x):
        linear = (x * self.linear).sum(1).unsqueeze(-1)
        interaction = self.second_order(x)
        res = linear + interaction

        return res


class SecondOrderInteraction(Module):
    """
    Factorized parameters for the Second Order Interactions

    Parameters
    ----------
    n_features: int
        Length of the input vector.
    n_factors: int, optional
        Number of factors of the factorized parameters
    """

    def __init__(self, n_features, n_factors):
        super(SecondOrderInteraction, self).__init__()
        self.batch_size = None
        self.n_features = n_features
        self.n_factors = n_factors

        self.v = Parameter(torch.Tensor(self.n_features, self.n_factors))
        self.v.data.uniform_(-0.01, 0.01)

    def forward(self, x):
        self.batch_size = x.size()[0]
        pow_x = torch.pow(x, 2)
        pow_v = torch.pow(self.v, 2)
        pow_sum = torch.pow(torch.mm(x, self.v), 2)
        sum_pow = torch.mm(pow_x, pow_v)
        out = 0.5 * (pow_sum - sum_pow).sum(1)

        return out.unsqueeze(-1)
