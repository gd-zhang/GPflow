# Copyright 2016 James Hensman, alexggmatthews
# Copyright 2017 Artem Artemev @awav
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import tensorflow as tf
import numpy as np
import pandas as pd

from . import settings


__TRAINABLES = tf.GraphKeys.TRAINABLE_VARIABLES
__GLOBAL_VARIABLES = tf.GraphKeys.GLOBAL_VARIABLES


def pretty_pandas_table(names, keys, values):
    df = pd.DataFrame(dict(zip(keys, values)))
    df.index = names
    df = df.reindex_axis(keys, axis=1)
    return df


def is_ndarray(value):
    return isinstance(value, np.ndarray)


def is_list(value):
    return isinstance(value, list)


def is_tensor(value):
    return isinstance(value, (tf.Tensor, tf.Variable))


def is_number(value):
    return (not isinstance(value, str)) and np.isscalar(value)


def is_valid_param_value(value):
    if isinstance(value, list):
        if not value:
            return False
        zero_val = value[0]
        arrays = (list, np.ndarray)
        scalars = (float, int)
        if isinstance(zero_val, scalars):
            types = scalars
        elif isinstance(zero_val, arrays):
            types = arrays
        else:
            return False
        return all(isinstance(val, types) for val in value[1:])
    return ((value is not None)
            and is_number(value)
            or is_ndarray(value)
            or is_tensor(value))

def normalize_num_type(num_type):
    """
    Work out what a sensible type for the array is. if the default type
    is float32, downcast 64bit float to float32. For ints, assume int32
    """
    if isinstance(num_type, tf.DType):
        num_type = num_type.as_numpy_dtype.type

    if num_type in [np.float32, np.float64]:  # pylint: disable=E1101
        num_type = settings.float_type
    elif num_type in [np.int16, np.int32, np.int64]:
        num_type = settings.int_type
    else:
        raise ValueError('Unknown dtype "{0}" passed to normalizer.'.format(num_type))

    return num_type


def vec_to_tri(vectors, N):
    """
    Takes a D x M tensor `vectors' and maps it to a D x matrix_size X matrix_sizetensor
    where the where the lower triangle of each matrix_size x matrix_size matrix is
    constructed by unpacking each M-vector.

    Native TensorFlow version of Custom Op by Mark van der Wilk.

    def int_shape(x):
        return list(map(int, x.get_shape()))

    D, M = int_shape(vectors)
    N = int( np.floor( 0.5 * np.sqrt( M * 8. + 1. ) - 0.5 ) )
    # Check M is a valid triangle number
    assert((matrix * (N + 1)) == (2 * M))
    """
    indices = list(zip(*np.tril_indices(N)))
    indices = tf.constant([list(i) for i in indices], dtype=tf.int64)

    def vec_to_tri_vector(vector):
        return tf.scatter_nd(indices=indices, shape=[N, N], updates=vector)

    return tf.map_fn(vec_to_tri_vector, vectors)