import tensorflow as tf
import numpy as np
import os

def max_pool_2x2(x):
    return tf.nn.max_pool(x, ksize=[1, 2, 2, 1],
                          strides=[1, 2, 2, 1], padding="SAME")

l2_regularizer = tf.contrib.layers.l2_regularizer(1e-5)
def _conv_bn_lrelu_pool(x, filters = 32, kernel_size = [5,5], pool = False, bn = True, bn_training = True):
	_conv = tf.layers.conv2d(x, filters = filters, kernel_size = kernel_size, strides=(1, 1), padding='same',
			kernel_initializer= 'truncated_normal', kernel_regularizer=l2_regularizer)
	if bn:
		_bn = tf.layers.batch_normalization(_conv, training = bn_training)
	else:
		_bn = _conv
	_lrelu = tf.nn.leaky_relu(_bn)
	if pool:
		_out = max_pool_2x2(_lrelu)
	else:
		_out = _lrelu
	return _out

def conv_block(x, nb_cnn = 4, bn = False, bn_training = True, filters = 32, kernel_size = [5,5], scope_name = 'encoder'):
	with tf.variable_scope(scope_name):
		h = _conv_bn_lrelu_pool(x, filters = filters, kernel_size = kernel_size, pool = False, bn = bn, bn_training = bn_training)
		for i in range(1, nb_cnn):
			if i%2 == 1:
				pool = True
			else:
				pool = False
			h = _conv_bn_lrelu_pool(h, filters = filters, kernel_size = kernel_size, pool = pool, bn = bn, bn_training = bn_training)
	return h

def _up_conv_bn_lrelu(x, filters = 32, kernel_size = [5,5], up = False, bn = True, bn_training = True):
	if up:
		x = tf.keras.layers.UpSampling2D()(x)
	_conv = _conv_bn_lrelu_pool(x, filters = filters, kernel_size = kernel_size, pool = False, bn = bn, bn_training = bn_training)
	return _conv

def up_conv_block(x, nb_cnn = 4, bn = False, bn_training = True, filters = 32, kernel_size = [5,5], scope_name = 'decoder'):
	with tf.variable_scope(scope_name):
		h = _up_conv_bn_lrelu(x, filters = filters, kernel_size = kernel_size, up = True, bn = bn, bn_training = bn_training)
		for i in range(1, nb_cnn):
			if i%2 == 1:
				up = False
			else:
				up = True
			h = _up_conv_bn_lrelu(h, filters = filters, kernel_size = kernel_size, up = up, bn = bn, bn_training = bn_training)
	return h

# x = tf.placeholder("float", shape = [None, 128, 128,1])
# h1 = conv_block(x, nb_cnn = 4, bn = False, filters = 32, kernel_size = [5,5], scope_name = 'encoder')
# h2 = up_conv_block(h1, nb_cnn = 4, bn = False, filters = 32, kernel_size = [5,5], scope_name = 'decoder')
# h3 = tf.layers.conv2d(h2, filters = 1, kernel_size = [5,5], strides=(1, 1), padding='same',
# 			kernel_initializer= 'truncated_normal', kernel_regularizer=l2_regularizer)

### create network
def auto_encoder(x, nb_cnn = 4, bn = False, bn_training = True, filters = 32, kernel_size = [5,5], scope_name = 'base', reuse = False):
	with tf.variable_scope(scope_name, reuse = reuse):
		h1 = conv_block(x, nb_cnn = nb_cnn, bn = bn, bn_training = bn_training, filters = filters, kernel_size = kernel_size, scope_name = 'encoder')
		h2 = up_conv_block(h1, nb_cnn = nb_cnn, bn = bn, bn_training = bn_training, filters = filters, kernel_size = kernel_size, scope_name = 'decoder')
		y = tf.layers.conv2d(h2, filters = 1, kernel_size = kernel_size, strides=(1, 1), padding='same',
					kernel_initializer= 'truncated_normal', kernel_regularizer=l2_regularizer)
		y = tf.nn.relu(y)
	return h1, h2, y

## auto-encoder version 2
def conv_block2(x, nb_cnn = 4, bn = False, filters = 32, kernel_size = [5,5], scope_name = 'encoder'):
	with tf.variable_scope(scope_name):
		h = _conv_bn_lrelu_pool(x, filters = filters, kernel_size = kernel_size, pool = True, bn = bn)
		for i in range(1, nb_cnn):
			h = _conv_bn_lrelu_pool(h, filters = filters, kernel_size = kernel_size, pool = True, bn = bn)
	return h

def up_conv_block2(x, nb_cnn = 4, bn = False, filters = 32, kernel_size = [5,5], scope_name = 'decoder'):
	with tf.variable_scope(scope_name):
		h = _up_conv_bn_lrelu(x, filters = filters, kernel_size = kernel_size, up = True, bn = bn)
		for i in range(1, nb_cnn):
			h = _up_conv_bn_lrelu(h, filters = filters, kernel_size = kernel_size, up = True, bn = bn)
	return h

def auto_encoder2(x, nb_cnn = 4, bn = False, filters = 32, kernel_size = [5,5], scope_name = 'base', reuse = False):
	with tf.variable_scope(scope_name, reuse = reuse):
		h1 = conv_block2(x, nb_cnn = nb_cnn, bn = bn, filters = filters, kernel_size = kernel_size, scope_name = 'encoder')
		h2 = up_conv_block2(h1, nb_cnn = nb_cnn, bn = bn, filters = filters, kernel_size = kernel_size, scope_name = 'decoder')
		if bn:
			h2 = tf.layers.batch_normalization(h2, training = True)
		y = tf.layers.conv2d(h2, filters = 1, kernel_size = kernel_size, strides=(1, 1), padding='same',
					kernel_initializer= 'truncated_normal', kernel_regularizer=l2_regularizer)
		y = tf.nn.relu(y)
	return h1, h2, y

def auto_encoder_stack(x, nb_cnn1 = 2, nb_cnn2 = 4, bn = False, filters = 32, kernel_size = [5,5], scope_name = 'base', reuse = False):
	with tf.variable_scope(scope_name, reuse = reuse):
		h1, h2, y1 = auto_encoder(x, nb_cnn = nb_cnn1, bn = False, filters = 32, kernel_size = [5,5], scope_name = 'block1', reuse = False)
		h1, h2, y2 = auto_encoder(x, nb_cnn = nb_cnn2, bn = False, filters = 32, kernel_size = [5,5], scope_name = 'block2', reuse = False)
	return y1, y2

def auto_encoder_stack2(x, nb_cnn1 = 2, nb_cnn2 = 4, bn = False, filters = 32, kernel_size = [5,5], scope_name = 'base', reuse = False):
	with tf.variable_scope(scope_name, reuse = reuse):
		h1, h2, y1 = auto_encoder2(x, nb_cnn = nb_cnn1, bn = False, filters = 32, kernel_size = [5,5], scope_name = 'block1', reuse = False)
		h1, h2, y2 = auto_encoder2(x, nb_cnn = nb_cnn2, bn = False, filters = 32, kernel_size = [5,5], scope_name = 'block2', reuse = False)
	return y1, y2