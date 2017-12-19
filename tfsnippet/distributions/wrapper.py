import contextlib

import tensorflow as tf
import zhusuan

from tfsnippet.utils import docstring_inherit
from .base import Distribution
from .utils import reduce_group_ndims

__all__ = ['as_distribution']


def as_distribution(distribution):
    """
    Convert a supported type of `distribution` into :class:`Distribution` type.

    Args:
        distribution: A supported distribution instance. Supported types are:

                      1.  :class:`Distribution`
                      2.  :class:`zhusuan.distributions.Distribution`.

    Returns:
        Distribution: The wrapped distribution of :class:`Distribution` type.

    Raises:
        TypeError: If the specified `distribution` cannot be converted.
    """
    if isinstance(distribution, Distribution):
        return distribution
    if isinstance(distribution, zhusuan.distributions.Distribution):
        return ZhuSuanDistribution(distribution)
    raise TypeError('Type `{}` cannot be casted into `tfsnippet.distributions.'
                    'Distribution`'.format(distribution.__class__.__name__))


class ZhuSuanDistribution(Distribution):
    """
    Wrapping a :class:`zhusuan.distributions.Distribution` into
    :class:`~tfsnippet.distributions.Distribution`.

    Args:
        distribution (zhusuan.distributions.Distribution):
            The distribution object from `ZhuSuan`_.
            `group_ndims` attribute of `distribution` would be totally ignored.

            Thread-safety is not guaranteed for using `distribution` outside
            of this wrapper, since it may temporarily modify internal flags
            of `distribution` within some methods.

    .. _`ZhuSuan`: https://github.com/thu-ml/zhusuan
    """

    def __init__(self, distribution):
        if not isinstance(distribution, zhusuan.distributions.Distribution):
            raise TypeError('`distribution` is not an instance of `zhusuan.'
                            'distributions.Distribution`')
        super(ZhuSuanDistribution, self).__init__()
        self._distribution = distribution

    def __repr__(self):
        return 'Distribution({!r})'.format(self._distribution)

    @property
    @docstring_inherit(Distribution.dtype)
    def dtype(self):
        return self._distribution.dtype

    @property
    @docstring_inherit(Distribution.is_continuous)
    def is_continuous(self):
        return self._distribution.is_continuous

    @property
    @docstring_inherit(Distribution.is_reparameterized)
    def is_reparameterized(self):
        return self._distribution.is_reparameterized

    @property
    @docstring_inherit(Distribution.value_shape)
    def value_shape(self):
        return self._distribution.value_shape

    @docstring_inherit(Distribution.get_value_shape)
    def get_value_shape(self):
        return self._distribution.get_value_shape()

    @property
    @docstring_inherit(Distribution.batch_shape)
    def batch_shape(self):
        return self._distribution.batch_shape

    @docstring_inherit(Distribution.get_batch_shape)
    def get_batch_shape(self):
        return self._distribution.get_batch_shape()

    @docstring_inherit(Distribution.sample)
    def sample(self, n_samples=None, is_reparameterized=None, group_ndims=0,
               name=None):
        from tfsnippet.stochastic import StochasticTensor

        if is_reparameterized and not self.is_reparameterized:
            raise RuntimeError('Distribution is not re-parameterized')
        elif is_reparameterized is False and self.is_reparameterized:
            @contextlib.contextmanager
            def set_is_reparameterized():
                try:
                    self._distribution._is_reparameterized = False
                    yield False
                finally:
                    self._distribution._is_reparameterized = True
        else:
            @contextlib.contextmanager
            def set_is_reparameterized():
                yield self.is_reparameterized

        with tf.name_scope(name=name, default_name='sample'):
            with set_is_reparameterized() as is_reparameterized:
                samples = self._distribution.sample(n_samples=n_samples)
                return StochasticTensor(
                    distribution=self,
                    tensor=samples,
                    n_samples=n_samples,
                    group_ndims=group_ndims,
                    is_reparameterized=is_reparameterized,
                )

    @docstring_inherit(Distribution.log_prob)
    def log_prob(self, given, group_ndims=0, name=None):
        with tf.name_scope(name=name, default_name='log_prob'):
            given = self._distribution._check_input_shape(given)
            log_prob = self._distribution._log_prob(given)
            return reduce_group_ndims(tf.reduce_sum, log_prob, group_ndims)

    @docstring_inherit(Distribution.prob)
    def prob(self, given, group_ndims=0, name=None):
        with tf.name_scope(name=name, default_name='prob'):
            given = self._distribution._check_input_shape(given)
            prob = self._distribution._prob(given)
            return reduce_group_ndims(tf.reduce_prod, prob, group_ndims)
