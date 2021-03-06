import tensorflow as tf
import tensorflow.math as tm
import math

import numpy as np
import os
import glob
from natsort import natsorted
from termcolor import colored 
import argparse
from sklearn.metrics import roc_auc_score
import scipy.io
import scipy.misc as misc
import matplotlib

from load_data import load_MRI_anomaly, load_MRI_anomaly_test
from models2 import auto_encoder, auto_encoder3, auto_encoder4
from helper_function import normalize_0_1, print_yellow, print_red, print_green, print_block
from helper_function import plot_hist, plot_LOSS, plot_AUC, plot_hist_pixels, plot_hist_list
from helper_function import generate_folder, save_recon_images, save_recon_images_v2, save_recon_images_v3, save_recon_images_v4 

## functions
def str2bool(value):
    return value.lower() == 'true'

gpu = 2; docker = True
os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu)

if docker:
# 	output_folder = '/data/results/MRI/MRI_AE'
	output_folder = '/data/results/MRI/'
else:
	output_folder = './data/MRI'

# model_name = 'AE1-MRI-cn-6-fr-32-ks-5-bn-False-lr-0.0001-stps-100000-bz-50-tr-65k-vl-400-test-1000-l-mse'
# model_name = 'AE1-MRI-cn-4-fr-32-ks-5-bn-False-lr-0.0001-stps-100000-bz-50-tr-65k-vl-400-test-1000-l-mse'
# model_name = 'AE4-MRI-cn-6-fr-32-ks-5-bn-False-lr-0.0001-stps-100000-bz-50-tr-65k-vl-400-test-1000-l-mae'
# model_name = 'AEL3-MRI-cn-4-fr-32-ks-5-bn-False-lr-0.0001-stps-100000-bz-50-tr-65k-vl-400-test-1000-l-mae'
model_name = 'AEL1-MRI-cn-4-fr-32-ks-5-bn-True-lr-1e-06-stps-100000-bz-50-tr-65k-vl-400-test-1000-l-mae-ano_w-0.05'

splits = model_name.split('-')
if len(splits[0])<=2:
	version =1
else:
	version = int(splits[0][-1])
for i in range(len(splits)):
	if splits[i] == 'cn':
		nb_cnn = int(splits[i+1])
	elif splits[i] == 'fr':
		filters = int(splits[i+1])
	elif splits[i] == 'bn':
		if splits[i+1]=='True':
			batch_norm = True
		else:
			batch_norm = False
	elif splits[i] == 'ks':
		kernel_size = int(splits[i+1])
	elif splits[i] == 'tr':
		train = int(splits[i+1][:2])* 1000
	elif splits[i] == 'vl':
		val = int(splits[i+1])
	elif splits[i] == 'test':
		test = int(splits[i+1])
	elif splits[i] == 'n' or splits[i]=='NL':
		noise = float(splits[i+1])
	elif splits[i] == 'l':
		loss = splits[i+1]


model_folder = os.path.join(output_folder, model_name)

## load data
print_red('Data loading ...')
version1, version2, version3, version4 = 0, 1, 4, 5
_, _, _, X_SP_tst = load_MRI_anomaly(docker = docker, train = train, val = val, normal = test, anomaly = test, version = version1)
_, _, X_SA_tst, X_SP_tst1 = load_MRI_anomaly(docker = docker, train = train, val = val, normal = test, anomaly = test, version = version2)
_, _, _, X_SP_tst2 = load_MRI_anomaly(docker = docker, train = train, val = val, normal = test, anomaly = test, version = version3)
_, _, _, X_SP_tst3 = load_MRI_anomaly(docker = docker, train = train, val = val, normal = test, anomaly = test, version = version4)
X_SA_tst, X_SP_tst1, X_SP_tst2, X_SP_tst3 = normalize_0_1(X_SA_tst), normalize_0_1(X_SP_tst1), normalize_0_1(X_SP_tst2), normalize_0_1(X_SP_tst3)
X_SP_tst = normalize_0_1(X_SP_tst)
## test data
Xt = np.concatenate([X_SA_tst, X_SP_tst1, X_SP_tst2, X_SP_tst3], axis = 0)
X_SP_tst = np.expand_dims(X_SP_tst, axis = 3)
#yt = np.concatenate([np.zeros((len(X_SA_tst),1)), np.ones((len(X_SP_tst1),1))], axis = 0).flatten()
## Dimension adjust
X_SA_tst, X_SP_tst1, X_SP_tst2, X_SP_tst3, Xt = np.expand_dims(X_SA_tst, axis = 3), np.expand_dims(X_SP_tst1, axis = 3), np.expand_dims(X_SP_tst2, axis = 3),\
		 np.expand_dims(X_SP_tst3, axis = 3), np.expand_dims(Xt, axis = 3)
print_red('Data Loaded !')

Xa = load_MRI_anomaly_test(dataset = 'null_mixed_4x'); Xa = normalize_0_1(Xa); Xa = np.expand_dims(Xa, axis = 3)

# batch_norm = True 
bn_training = False
scope = 'base'
x = tf.placeholder("float", shape=[None, 256, 256, 1])
is_training = tf.placeholder_with_default(False, (), 'is_training')

if version == 1 or version == 2:
	h1, h2, y = auto_encoder(x, nb_cnn = nb_cnn, bn = batch_norm, bn_training = is_training, filters = filters, kernel_size = [kernel_size, kernel_size], scope_name = scope)
elif version == 3:
	h1, h2, y = auto_encoder3(x, nb_cnn = nb_cnn, bn = batch_norm, bn_training = is_training, filters = filters, kernel_size = [kernel_size, kernel_size], scope_name = scope)
elif version == 4:
	h1, h2, y = auto_encoder4(x, nb_cnn = nb_cnn, bn = batch_norm, bn_training = is_training, filters = filters, kernel_size = [kernel_size, kernel_size], scope_name = scope)

if loss == 'mse':
	err_map = tf.square(y - x)
elif loss == 'mae':
	err_map = tf.abs(y - x)

# tf.keras.backend.clear_session()
# create a saver
vars_list = tf.global_variables(scope)
key_list = [v.name[:-2] for v in tf.global_variables(scope)]
key_direct = {}
for key, var in zip(key_list, vars_list):
	key_direct[key] = var
saver = tf.train.Saver(key_direct, max_to_keep=1)

# print out trainable parameters
for v in key_list:
	print_green(v)

def evaluate(sess, y, x, is_training, err_map, X_tst, batch_size = 100):
	y_list, err_map_list = [], []
	i = 0
	while batch_size*i < X_tst.shape[0]:
		batch_x = X_tst[batch_size*i: min(batch_size*(i+1), X_tst.shape[0]),:]
		y_recon = y.eval(session = sess, feed_dict = {x:batch_x,is_training: False})
		y_list.append(y_recon)
		err_map_list.append(err_map.eval(session = sess, feed_dict = {x:batch_x,is_training: False}))
		i = i +1
	y_arr, err_map_arr = np.concatenate(y_list, axis = 0), np.concatenate(err_map_list, axis = 0)
	return y_arr, err_map_arr



# evaluate the reconstruction errs
with tf.Session() as sess:
	tf.global_variables_initializer().run(session=sess)
# 	saver.restore(sess, model_folder+'/best')
	saver.restore(sess, model_folder+'/model-40000')
	# norm
	Yn, norm_err_map = evaluate(sess, y, x, is_training, err_map, X_SA_tst, batch_size = 100)
	Ya, anom_err_map = evaluate(sess, y, x, is_training, err_map, X_SP_tst, batch_size = 100)
	Ya1, anom_err_map1 = evaluate(sess, y, x, is_training, err_map, X_SP_tst1, batch_size = 100)
	Ya2, anom_err_map2 = evaluate(sess, y, x, is_training, err_map, X_SP_tst2, batch_size = 100)
	Ya3, anom_err_map3 = evaluate(sess, y, x, is_training, err_map, X_SP_tst3, batch_size = 100)
	Ya4, anom_err_map4 = evaluate(sess, y, x, is_training, err_map, Xa, batch_size = 100)
	
	norm_recon_errs = np.apply_over_axes(np.mean, norm_err_map, [1,2,3]).flatten()
	anom_recon_errs = np.apply_over_axes(np.mean, anom_err_map, [1,2,3]).flatten()
	anom_recon_errs1 = np.apply_over_axes(np.mean, anom_err_map1, [1,2,3]).flatten()
	anom_recon_errs2 = np.apply_over_axes(np.mean, anom_err_map2, [1,2,3]).flatten()
	anom_recon_errs3 = np.apply_over_axes(np.mean, anom_err_map3, [1,2,3]).flatten()
	anom_recon_errs4 = np.apply_over_axes(np.mean, anom_err_map4, [1,2,3]).flatten()
	
	imgs = np.concatenate([X_SA_tst, X_SP_tst1, X_SP_tst2, X_SP_tst3], axis = 0)
	recons = np.concatenate([Yn, Ya1, Ya2, Ya3], axis = 0)
	err_maps = np.concatenate([norm_err_map, anom_err_map, anom_err_map1, anom_err_map2, anom_err_map3], axis = 0)
	recon_errs = np.concatenate([norm_recon_errs, anom_recon_errs, anom_recon_errs1, anom_recon_errs2, anom_recon_errs3], axis = 0)
	total_errs = np.concatenate([norm_recon_errs, anom_recon_errs, anom_recon_errs1, anom_recon_errs2, anom_recon_errs3, anom_recon_errs4], axis = 0)
# 	recon_errs = np.apply_over_axes(np.mean, err_maps, [1,2,3]).flatten()
# 	print_yellow('AUC: AE {0:.4f} AE(compare) {1:.4f} AE(normalized) {2:.4f} MP: {3:.4f}'.format(AE_auc, AE_auc1, AE_auc_n, MP_auc))
	print(model_name)
	result_folder = model_folder + '/detection_results'
	generate_folder(result_folder)
	np.savetxt(os.path.join(result_folder,'norm_stat.txt'), norm_recon_errs)
	np.savetxt(os.path.join(result_folder,'anom_stat.txt'), anom_recon_errs)
	np.savetxt(os.path.join(result_folder,'anom_stat1.txt'), anom_recon_errs1)
	np.savetxt(os.path.join(result_folder,'anom_stat2.txt'), anom_recon_errs2)
	np.savetxt(os.path.join(result_folder,'anom_stat3.txt'), anom_recon_errs3)
	np.savetxt(os.path.join(result_folder,'anom_stat4.txt'), anom_recon_errs4)

	## plot err histogram and recon images
	idx, idx1, idx2, idx3 = int(len(recon_errs)*1/5), int(len(recon_errs)*2/5), int(len(recon_errs)*3/5), int(len(recon_errs)*4/5)
	err_stat_list = [recon_errs[:idx], recon_errs[idx:idx1], recon_errs[idx1:idx2], recon_errs[idx2:idx3],recon_errs[idx3:]]
	min_value, max_value = np.min(total_errs), np.max(total_errs)
	print_green('Length: norm {} anom1 {} anom2 {} anom3 {}'.format(len(recon_errs[:idx1]), len(recon_errs[idx1:idx2]), len(recon_errs[idx2:idx3]), len(recon_errs[idx3:])))
	plot_hist_list(result_folder+'/hist-d-true-{}.png'.format(model_name), err_stat_list, ['True', 'f_meas_x4', 'f_meas_null_x2', 'f_meas_x2', 'f_meas_x3'], ['g', 'c', 'r', 'b', 'y'], [min_value, max_value])
	plot_hist_list(result_folder+'/hist-{}-{}.png'.format('meas_4x', model_name), [recon_errs[:idx], recon_errs[idx:idx1]], ['f_true', 'f_meas_4x'], ['g', 'c'], [min_value, max_value])
	plot_hist_list(result_folder+'/hist-{}-{}.png'.format('null_2x', model_name), [recon_errs[:idx], recon_errs[idx1:idx2]], ['f_true', 'f_null_2x'], ['g', 'r'], [min_value, max_value])
	plot_hist_list(result_folder+'/hist-{}-{}.png'.format('meas_2x', model_name), [recon_errs[:idx], recon_errs[idx2:idx3]], ['f_true', 'f_meas_2x'], ['g', 'b'], [min_value, max_value])
	plot_hist_list(result_folder+'/hist-{}-{}.png'.format('meas_3x', model_name), [recon_errs[:idx], recon_errs[idx3:]], ['f_true','f_meas_3x'], ['g', 'y'], [min_value, max_value])
	plot_hist_list(result_folder+'/hist-{}-{}.png'.format('null_mixed_4x', model_name), [recon_errs[:idx], anom_recon_errs4], ['f_true','f_mixed_4x'], ['g', 'y'], [min_value, max_value])
	save_recon_images_v2(result_folder+'/recon-{}.png'.format(model_name), Xt, recons, err_maps, fig_size = [11,10])
	save_recon_images_v3(result_folder+'/recon_meas_4x-{}.png'.format(model_name), X_SP_tst, Ya, anom_err_map, fig_size = [11,20])
	save_recon_images_v3(result_folder+'/recon_meas_3x-{}.png'.format(model_name), X_SP_tst3, Ya3, anom_err_map3, fig_size = [11,20])
	save_recon_images_v3(result_folder+'/recon_null_mixed_4x-{}.png'.format(model_name), Xa, Ya4, anom_err_map4, fig_size = [11,20])
	save_recon_images_v3(result_folder+'/recon_true-{}.png'.format(model_name), X_SA_tst, Yn, norm_err_map, fig_size = [11,20])
	matplotlib.pyplot.imsave(result_folder+ '/closest_null_mixed_4x.png', np.squeeze(Ya4[np.argmin(anom_recon_errs4),:]))
	err_distance = np.abs(norm_recon_errs-anom_recon_errs3)
	err_distance_copy = np.copy(err_distance)
	distance_map = np.abs(np.tile(norm_recon_errs.reshape(-1,1), (1, len(norm_recon_errs)))-np.tile(anom_recon_errs3.reshape(1,-1), (len(anom_recon_errs3), 1)))
	distance_map_copy = np.copy(distance_map)
	nb_select = 100
	x_select_list, y_select_list = [], []
	for i in range(nb_select):
		x_indx, y_indx = np.where(distance_map_copy == np.min(distance_map_copy)); x_select_list.append(x_indx[0]); y_select_list.append(y_indx[0])
		distance_map_copy[x_indx[0], y_indx[0]] = np.inf
		print('Select {} {}-pair'.format(x_indx[0], y_indx[0]))
	norm_images, anom_images = X_SA_tst[x_select_list,:], X_SP_tst[y_select_list,:]
	save_recon_images_v4(result_folder+'/recon_close_err1-{}.png'.format(model_name), norm_images[:24,:], anom_images[:24,:], fig_size = [22,20])
	save_recon_images_v4(result_folder+'/recon_close_err2-{}.png'.format(model_name), norm_images[24:48,:], anom_images[24:48,:], fig_size = [22,20])
## test artifact with undersampling x4
# anom_recon_errs = np.apply_over_axes(np.mean, norm_err_map, [1,2,3]).flatten()
# max_value, min_value = np.min(np.concatenate([norm_recon_errs, anom_recon_errs])), np.max(np.concatenate([norm_recon_errs, anom_recon_errs]))
# plot_hist_list(result_folder+'/hist0-{}.png'.format(model_name), [norm_recon_errs, anom_recon_errs], ['Norm', 'Artifact_x_4'], ['g', 'm'], [max_value, min_value])

def evaluate_hidden(sess, y, h1, x, is_training, err_map, X_tst, batch_size = 100):
	h_list, y_list, err_map_list = [], [], []
	i = 0
	while batch_size*i < X_tst.shape[0]:
		batch_x = X_tst[batch_size*i: min(batch_size*(i+1), X_tst.shape[0]),:]
		y_recon = y.eval(session = sess, feed_dict = {x:batch_x,is_training: False})
		h_out = h1.eval(session = sess, feed_dict = {x:batch_x,is_training: False})
		y_list.append(y_recon); h_list.append(h_out)
		err_map_list.append(err_map.eval(session = sess, feed_dict = {x:batch_x,is_training: False}))
		i = i +1
	h_arr, y_arr, err_map_arr = np.concatenate(h_list, axis = 0), np.concatenate(y_list, axis = 0), np.concatenate(err_map_list, axis = 0)
	return h_arr, y_arr, err_map_arr

## evaluate the norm of hiden features
with tf.Session() as sess:
	tf.global_variables_initializer().run(session=sess)
	saver.restore(sess, model_folder+'/best')
	# norm
	hn,  Yn, norm_err_map = evaluate_hidden(sess, y, h1, x, is_training, err_map, X_SA_tst, batch_size = 100)
	ha,  Ya, anom_err_map = evaluate_hidden(sess, y, h1, x, is_training, err_map, X_SP_tst, batch_size = 100)
	ha1, Ya1, anom_err_map1 = evaluate_hidden(sess, y, h1, x, is_training, err_map, X_SP_tst1, batch_size = 100)
	ha2, Ya2, anom_err_map2 = evaluate_hidden(sess, y, h1, x, is_training, err_map, X_SP_tst2, batch_size = 100)
	ha3, Ya3, anom_err_map3 = evaluate_hidden(sess, y, h1, x, is_training, err_map, X_SP_tst3, batch_size = 100)

norm_recon_errs = np.apply_over_axes(np.mean, norm_err_map, [1,2,3]).flatten()
anom_recon_errs1 = np.apply_over_axes(np.mean, anom_err_map1, [1,2,3]).flatten()
anom_recon_errs2 = np.apply_over_axes(np.mean, anom_err_map2, [1,2,3]).flatten()
anom_recon_errs3 = np.apply_over_axes(np.mean, anom_err_map3, [1,2,3]).flatten()
hn_norm = np.linalg.norm(hn.reshape(hn.shape[0], -1), ord = 2, axis = 1)
hn_anom = np.linalg.norm(ha.reshape(ha.shape[0], -1), ord = 2, axis = 1)
hn_anom1 = np.linalg.norm(ha1.reshape(ha1.shape[0], -1), ord = 2, axis = 1)
hn_anom2 = np.linalg.norm(ha2.reshape(ha2.shape[0], -1), ord = 2, axis = 1)
hn_anom3 = np.linalg.norm(ha3.reshape(ha3.shape[0], -1), ord = 2, axis = 1)
max_value, min_value = np.min(np.concatenate([hn_norm, hn_anom1, hn_anom2, hn_anom3])), np.max(np.concatenate([hn_norm, hn_anom1, hn_anom2, hn_anom3]))
result_folder = model_folder + '/detection_results'
plot_hist_list(result_folder+'/hist-norm1-{}.png'.format(model_name), [hn_norm, hn_anom1], ['Norm','Anomaly1'], ['g', 'r'], [max_value, min_value], xlabel = 'l2-norm')
plot_hist_list(result_folder+'/hist-norm2-{}.png'.format(model_name), [hn_norm, hn_anom2], ['Norm','Anomaly2'], ['g', 'b'], [max_value, min_value], xlabel = 'l2-norm')
plot_hist_list(result_folder+'/hist-norm3-{}.png'.format(model_name), [hn_norm, hn_anom3], ['Norm','Anomaly3'], ['g', 'y'], [max_value, min_value], xlabel = 'l2-norm')
plot_hist_list(result_folder+'/hist-norm4-{}.png'.format(model_name), [hn_norm, hn_anom1, hn_anom2, hn_anom3], ['Norm','Anomaly1', 'Anomaly2', 'Anomaly3'], ['g','r','b','y'], [max_value, min_value], xlabel = 'l2-norm')

## top 10 smallest reconstruction errs for a fixed f_meas
anom_recon_errs1_copy = np.copy(anom_recon_errs1)
nb_select = 10; index_list = []
for i in range(nb_select):
	min_index = np.argmin(anom_recon_errs1_copy); index_list.append(min_index); anom_recon_errs1_copy[min_index]= np.inf;
selected_images = X_SP_tst1[index_list,:]
dataset_folder = '/data/datasets/MRI'
full_data = np.load(dataset_folder + '/axial_batch2_256x256.npy')
true_image = full_data[66400,:]
save_recon_images_v5(result_folder+'/recon_top_10_err-{}.png'.format(model_name), np.concatenate([true_image.reshape(1,256,256,1),selected_images]), fig_size = [18,14])