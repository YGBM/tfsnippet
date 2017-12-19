import tensorflow as tf

from tfsnippet.utils import (TensorWrapper, register_tensor_wrapper_class,
                             TensorArgValidator)

__all__ = ['StochasticTensor']


class StochasticTensor(TensorWrapper):
    """
    Samples or observations of a stochastic variable.

    :class:`StochasticTensor` is a tensor-like object, carrying samples
    or observations of a random variable, following some `distribution`n
    of a specific :class:`Distribution` type.

    It mimics the interface of :class:`zhusuan.model.StochasticTensor`,
    except that it does not carry a `name`, and does not add itself to
    any :class:`BayesianNet` context automatically.
    This modified design fits the concept of :class:`~tfsnippet.modules.Module`
    better than the original :class:`zhusuan.model.StochasticTensor`.

    Args:
        distribution (tfsnippet.distributions.Distribution):
            The distribution of this :class:`StochasticTensor`.

        tensor (tf.Tensor or TensorWrapper):
            The samples or observations of this :class:`StochasticTensor`.

        n_samples (tf.Tensor or int):
            The number of samples taken in :class:`Distribution.sample`.
            If not :obj:`None`, the first dimension of `tensor` should be
            considered as the sampling dimension.

        group_ndims (int or tf.Tensor):
            The number of dimensions to be considered as events group in
            samples. (default 0)

        is_reparameterized (bool):
            Whether or not the samples are re-parameterized?  If not specified,
            will inherit `is_reparameterized` attribute from `distribution`.
    """

    def __init__(self, distribution, tensor, n_samples=None,
                 group_ndims=0, is_reparameterized=None):
        from tfsnippet.distributions import validate_group_ndims

        if is_reparameterized is None:
            is_reparameterized = distribution.is_reparameterized

        if n_samples is not None:
            with tf.name_scope('validate_n_samples'):
                validator = TensorArgValidator('n_samples')
                n_samples = validator.require_non_negative(
                    validator.require_int32(n_samples)
                )

        group_ndims = validate_group_ndims(group_ndims)

        super(StochasticTensor, self).__init__()
        self._self_distribution = distribution
        self._self_tensor = tf.convert_to_tensor(tensor)
        self._self_n_samples = n_samples
        self._self_group_ndims = group_ndims
        self._self_is_reparameterized = is_reparameterized
        self._self_log_prob = None
        self._self_prob = None

    def __repr__(self):
        return 'StochasticTensor({!r})'.format(self.tensor)

    def __hash__(self):
        # necessary to support Python's collection membership operators
        return id(self)

    def __eq__(self, other):
        # necessary to support Python's collection membership operators
        return self is other

    @property
    def distribution(self):
        """
        Get the :class:`Distribution` of this :class:`StochasticTensor`.

        Returns:
            Distribution: The distribution instance.
        """
        return self._self_distribution

    @property
    def n_samples(self):
        """
        Get the number of samples taken in :class:`Distribution.sample`.

        Returns:
            int or tf.Tensor or None: The number of samples.
        """
        return self._self_n_samples

    @property
    def group_ndims(self):
        """
        Get the number of dimensions to be considered as events group.

        Returns:
            int or tf.Tensor: The configured `group_ndims`.
        """
        return self._self_group_ndims

    @property
    def tensor(self):
        """
        Get the samples or observations `tensor`.

        Returns:
            tf.Tensor: The `tensor` specified at construction.
        """
        return self._self_tensor

    @property
    def is_continuous(self):
        """
        Whether or not this :class:`StochasticTensor` is continuous?

        Returns:
            bool: Equivalent to ``self.distribution.is_continuous``.
        """
        return self.distribution.is_continuous

    @property
    def is_reparameterized(self):
        """
        Whether or not this :class:`StochasticTensor` is re-parameterized?

        Returns:
            bool: A boolean indicating whether it is re-parameterized.
        """
        return self._self_is_reparameterized

    def log_prob(self, group_ndims=None):
        """
        Compute the log probability densities of this :class:`StochasticTensor`.

        Args:
            group_ndims (int or tf.Tensor):
                If specified, overriding the configured `group_ndims`.

        Returns:
            tf.Tensor: The log probability densities.
        """
        if group_ndims is None or group_ndims == self.group_ndims:
            if self._self_log_prob is None:
                self._self_log_prob = \
                    self.distribution.log_prob(self.tensor, self.group_ndims)
            return self._self_log_prob
        else:
            return self.distribution.log_prob(self.tensor, group_ndims)

    def prob(self, group_ndims=None):
        """
        Compute the probability densities of this :class:`StochasticTensor`.

        Args:
            group_ndims (int or tf.Tensor):
                If specified, overriding the configured `group_ndims`.

        Returns:
            tf.Tensor: The probability densities.
        """
        if group_ndims is None or group_ndims == self.group_ndims:
            if self._self_prob is None:
                self._self_prob = \
                    self.distribution.prob(self.tensor, self.group_ndims)
            return self._self_prob
        else:
            return self.distribution.prob(self.tensor, group_ndims)


register_tensor_wrapper_class(StochasticTensor)
