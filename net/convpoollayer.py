"""Provides ConvLayer class for using in CNNs.

ConvLayer provides interface for building convolutional layers in CNNs.
ConvLayerParams is the parametrization of these ConvLayer layers.

Copyright 2015 Markus Oberweger, ICG,
Graz University of Technology <oberweger@icg.tugraz.at>

This file is part of DeepPrior.

DeepPrior is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

DeepPrior is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with DeepPrior.  If not, see <http://www.gnu.org/licenses/>.
"""

import numpy
from net.layer import Layer
from net.layerparams import LayerParams

__author__ = "Paul Wohlhart <wohlhart@icg.tugraz.at>, Markus Oberweger <oberweger@icg.tugraz.at>"
__copyright__ = "Copyright 2015, ICG, Graz University of Technology, Austria"
__credits__ = ["Paul Wohlhart", "Markus Oberweger"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Markus Oberweger"
__email__ = "oberweger@icg.tugraz.at"
__status__ = "Development"


class ConvPoolLayerParams(LayerParams):

    def __init__(self, inputDim=None, nFilters=None, filterDim=None, activation=None, poolsize=(1, 1), poolType=0,
                 filter_shape=None, image_shape=None, outputDim=None, stride=(1, 1), border_mode='valid', hasBias=True,
                 init_method=None):
        """
        :type filter_shape: tuple or list of length 4
        :param filter_shape: (number of filters, num inputVar feature maps, filter height,filter width)

        :type image_shape: tuple or list of length 4
        :param image_shape: (batch size, num inputVar feature maps, image height, image width)

        :type poolsize: tuple or list of length 2
        :param poolsize: the downsampling (pooling) factor (#rows,#cols)
        """

        super(ConvPoolLayerParams, self).__init__(inputDim, outputDim)

        self._nFilters = nFilters
        self._filterDim = filterDim
        self._poolsize = poolsize
        self._poolType = poolType
        self._filter_shape = filter_shape
        self._image_shape = image_shape
        self._activation = activation
        self._hasbias = hasBias
        self._stride = stride
        self._border_mode = 'half' if border_mode == 'same' else border_mode
        self._init_method = init_method
        self.update()

    @property
    def filter_shape(self):
        return self._filter_shape

    @property
    def image_shape(self):
        return self._image_shape

    @property
    def stride(self):
        return self._stride

    @stride.setter
    def stride(self, value):
        self._stride = value
        self.update()

    @property
    def border_mode(self):
        return self._border_mode

    @border_mode.setter
    def border_mode(self, value):
        if value == 'same':
            value = 'half'
        self._border_mode = value
        self.update()

    @property
    def nFilters(self):
        return self._nFilters

    @nFilters.setter
    def nFilters(self, value):
        self._nFilters = value
        self.update()

    @property
    def filterDim(self):
        return self._filterDim

    @filterDim.setter
    def filterDim(self, value):
        self._filterDim = value
        self.update()

    @property
    def poolsize(self):
        return self._poolsize

    @poolsize.setter
    def poolsize(self, value):
        self._poolsize = value
        self.update()

    @property
    def poolType(self):
        return self._poolType

    @property
    def activation(self):
        return self._activation

    @activation.setter
    def activation(self, value):
        self._activation = value

    @property
    def hasBias(self):
        return self._hasbias

    @hasBias.setter
    def hasBias(self, value):
        self._hasbias = value

    def update(self):
        """
        calc image_shape,
        """
        self._filter_shape = (self._nFilters,
                              self._inputDim[1],
                              self._filterDim[0],
                              self._filterDim[1])
        self._image_shape = self._inputDim

        if self._border_mode == 'valid':
            self._outputDim = (self._inputDim[0],   # batch_size
                               self._nFilters,      # number of kernels
                               (self._inputDim[2] - self._filterDim[0] + 1),   # output H
                               (self._inputDim[3] - self._filterDim[1] + 1))   # output W
        elif self._border_mode == 'full':
            self._outputDim = (self._inputDim[0],   # batch_size
                               self._nFilters,      # number of kernels
                               (self._inputDim[2] + self._filterDim[0] - 1),   # output H
                               (self._inputDim[3] + self._filterDim[1] - 1))   # output W
        elif self._border_mode == 'half':
            self._outputDim = (self._inputDim[0],   # batch_size
                               self._nFilters,      # number of kernels
                               self._inputDim[2],   # output H
                               self._inputDim[3])   # output W
        else:
            raise ValueError("Unknown border mode")

        # correct stride
        self._outputDim = list(self._outputDim)
        self._outputDim[2] = int(numpy.ceil(self._outputDim[2] / float(self._stride[0]))) // self._poolsize[0]
        self._outputDim[3] = int(numpy.ceil(self._outputDim[3] / float(self._stride[1]))) // self._poolsize[1]
        self._outputDim = tuple(self._outputDim)

        # no pooling required
        if(self._poolsize[0] == 1) and (self._poolsize[1] == 1):
            self._poolType = -1

    def getMemoryRequirement(self):
        """
        Get memory requirements of weights
        :return: memory requirement
        """
        return (numpy.prod(self.filter_shape) + self.filter_shape[0]) * 4  # sizeof(theano.config.floatX)


class ConvPoolLayer(Layer):
    """
    Pool Layer of a convolutional network

    copy of LeNetConvPoolLayer from deeplearning.net tutorials
    """

    def __init__(self, rng, inputVar, cfgParams, copyLayer=None, layerNum=None):
        """
        Allocate a LeNetConvPoolLayer with shared variable internal parameters.

        :type rng: numpy.random.RandomState
        :param rng: a random number generator used to initialize weights

        :type inputVar: theano.tensor.dtensor4
        :param inputVar: symbolic image tensor, of shape image_shape

        :type cfgParams: ConvPoolLayerParams
        """
        import theano
        import theano.tensor as T
        from theano.tensor.signal.pool import pool_2d
        from theano.tensor.nnet import conv2d

        super(ConvPoolLayer, self).__init__(rng)

        assert isinstance(cfgParams, ConvPoolLayerParams)

        floatX = theano.config.floatX  # @UndefinedVariable

        filter_shape = cfgParams.filter_shape
        image_shape = cfgParams.image_shape
        filter_stride = cfgParams.stride
        poolsize = cfgParams.poolsize
        poolType = cfgParams.poolType
        activation = cfgParams.activation
        inputDim = cfgParams.inputDim
        border_mode = cfgParams.border_mode

        self.cfgParams = cfgParams
        self.layerNum = layerNum

        assert image_shape[1] == filter_shape[1]
        self.inputVar = inputVar

        if not (copyLayer is None):
            self.W = copyLayer.W
        else:
            wInitVals = self.getInitVals(filter_shape, 'conv', act_fn=cfgParams.activation_str, orthogonal=False, method=cfgParams._init_method)
            self.W = theano.shared(wInitVals, borrow=True, name='convW{}'.format(layerNum))

        # the bias is a 1D tensor -- one bias per output feature map
        if self.cfgParams.hasBias is True:
            if not (copyLayer is None):
                self.b = copyLayer.b
            else:
                b_values = numpy.zeros((filter_shape[0],), dtype=floatX)
                self.b = theano.shared(value=b_values, borrow=True, name='convB{}'.format(layerNum))

        # convolve inputVar feature maps with filters
        conv_out = conv2d(input=inputVar,
                          filters=self.W,
                          filter_shape=filter_shape,
                          input_shape=image_shape,
                          subsample=filter_stride,
                          border_mode=border_mode)

        # downsample each feature map individually, using maxpooling
        if poolType == 0:
            # use maxpooling
            pooled_out = pool_2d(input=conv_out, ds=poolsize, ignore_border=True, mode='max')
        elif poolType == 1:
            # use average pooling
            pooled_out = pool_2d(input=conv_out, ds=poolsize, ignore_border=True, mode='average_inc_pad')
        elif poolType == 3:
            # use subsampling and ignore border
            pooled_out = conv_out[:, :, :(inputDim[2]//poolsize[0])*poolsize[0], :(inputDim[3]//poolsize[1])*poolsize[1]][:, :, ::2, ::2]
        elif poolType == -1:
            # no pooling at all
            pooled_out = conv_out
        else:
            raise NotImplementedError()

        # add the bias term. Since the bias is a vector (1D array), we first reshape it to a tensor of shape
        # (1,n_filters,1,1). Each bias will thus be broadcasted across mini-batches and feature map width & height
        if self.cfgParams.hasBias is True:
            lin_output = pooled_out + self.b.dimshuffle('x', 0, 'x', 'x')
        else:
            lin_output = pooled_out
        self.output_pre_act = lin_output
        self.output = (lin_output if activation is None
                       else activation(lin_output))

        self.output.name = 'output_layer_{}'.format(self.layerNum)

        # store parameters of this layer
        self.params = [self.W, self.b] if self.cfgParams.hasBias else [self.W]
        self.weights = [self.W]

    def __str__(self):
        """
        Print configuration of layer
        :return: configuration string
        """
        return "inputDim {}, outputDim {}, filterDim {}, nFilters {}, activation {}, stride {}, border_mode {}, " \
               "hasBias {}, pool_type {}, pool_size {}".format(self.cfgParams.inputDim,
                                                               self.cfgParams.outputDim,
                                                               self.cfgParams.filterDim,
                                                               self.cfgParams.nFilters,
                                                               self.cfgParams.activation_str,
                                                               self.cfgParams.stride,
                                                               self.cfgParams.border_mode,
                                                               self.cfgParams.hasBias,
                                                               self.cfgParams.poolType,
                                                               self.cfgParams.poolsize)
