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

from load_data import *
from models import *

## functions
def str2bool(value):
    return value.lower() == 'true'

def normalize_0_1(data):
	data = np.squeeze(data)
	shp = data.shape
	_shp = (shp[0],)
	for i in range(1,len(shp)):
		_shp = _shp + (1,)
	data = (data - np.amin(np.amin(data, axis = -1), axis = -1).reshape(_shp))/\
			(np.amax(np.amax(data, axis = -1), axis = -1).reshape(_shp)-\
			np.amin(np.amin(data, axis = -1), axis = -1).reshape(_shp))
	image_sum = np.squeeze(np.apply_over_axes(np.sum, data, axes = [1,2]))
	return data[~np.isnan(image_sum),:]

def pad_128(data):
	return np.pad(data, ((0,0),(10,9),(10,9)), 'mean')

def print_yellow(str):
	from termcolor import colored 
	print(colored(str, 'yellow'))

def print_red(str):
	from termcolor import colored 
	print(colored(str, 'red'))

def print_green(str):
	from termcolor import colored 
	print(colored(str, 'green'))

def print_block(symbol = '*', nb_sybl = 70):
	print_green(symbol*nb_sybl)

def plot_LOSS(file_name, skip_points, train_loss_list, val_loss_list, norm_loss_list, abnorm_loss_list):
	import matplotlib.pyplot as plt
	from matplotlib.backends.backend_agg import FigureCanvasAgg
	from matplotlib.figure import Figure
	fig_size = (8,6)
	fig = Figure(figsize=fig_size)
	file_name = file_name
	ax = fig.add_subplot(111)
	if len(train_loss_list) < skip_points:
		return
	ax.plot(train_loss_list[skip_points:])
	ax.plot(val_loss_list[skip_points:])
	ax.plot(norm_loss_list[skip_points:])
	ax.plot(abnorm_loss_list[skip_points:])
	title = os.path.basename(os.path.dirname(file_name))
	ax.set_title(title)
	ax.set_xlabel('Iterations/100')
	ax.set_ylabel('MSE')
	ax.legend(['Train','Valid','T-norm', 'T-Abnorm'])
	ax.set_xlim([0,len(train_loss_list)])
	canvas = FigureCanvasAgg(fig)
	canvas.print_figure(file_name, dpi=100)

# visualize one group of examples
def save_recon_images_1(img_file_name, imgs, recons, fig_size):
	from matplotlib.backends.backend_agg import FigureCanvasAgg
	from matplotlib.figure import Figure
	imgs, recons = np.squeeze(imgs), np.squeeze(recons)
	test_size = imgs.shape[0]
	indxs = np.random.randint(0,int(test_size),3)
# 	fig_size = (8,6)
	fig_size = fig_size
	fig = Figure(figsize=fig_size)
	rows, cols = 2, 3
	ax = fig.add_subplot(rows, cols, 1); cax=ax.imshow(imgs[indxs[0],:],cmap='gray'); fig.colorbar(cax); ax.set_title('Image-{}'.format(indxs[0])); ax.set_ylabel('f') 
	ax = fig.add_subplot(rows, cols, 2); cax=ax.imshow(imgs[indxs[1],:],cmap='gray'); fig.colorbar(cax); ax.set_title('Image-{}'.format(indxs[1]));
	ax = fig.add_subplot(rows, cols, 3); cax=ax.imshow(imgs[indxs[2],:],cmap='gray'); fig.colorbar(cax); ax.set_title('Image-{}'.format(indxs[2]));
	ax = fig.add_subplot(rows, cols, 4); cax=ax.imshow(recons[indxs[0],:],cmap='gray'); fig.colorbar(cax); ax.set_ylabel('f_MP')
	ax = fig.add_subplot(rows, cols, 5); cax=ax.imshow(recons[indxs[1],:],cmap='gray'); fig.colorbar(cax);
	ax = fig.add_subplot(rows, cols, 6); cax=ax.imshow(recons[indxs[2],:],cmap='gray'); fig.colorbar(cax);
	canvas = FigureCanvasAgg(fig)
	canvas.print_figure(img_file_name, dpi=100)

def plot_hist(file_name, x, y):
	import matplotlib.pyplot as plt
	from matplotlib.backends.backend_agg import FigureCanvasAgg
	from matplotlib.figure import Figure
	kwargs = dict(alpha=0.6, bins=100, density= False, stacked=True)
	fig_size = (8,6)
	fig = Figure(figsize=fig_size)
	file_name = file_name
	ax = fig.add_subplot(111)
	ax.hist(x, **kwargs, color='g', label='Norm')
	ax.hist(y, **kwargs, color='r', label='Anomaly')
	title = os.path.basename(os.path.dirname(file_name))
	ax.set_title(title)
	ax.set_xlabel('Error')
	ax.set_ylabel('Frequency')
	ax.legend(['Norm', 'Anomaly'])
	ax.set_xlim([np.min(np.concatenate([x,y])), np.max(np.concatenate([x,y]))])
	canvas = FigureCanvasAgg(fig)
	canvas.print_figure(file_name, dpi=100)

def plot_hist_pixels(file_name, x, y):
	import matplotlib.pyplot as plt
	from matplotlib.backends.backend_agg import FigureCanvasAgg
	from matplotlib.figure import Figure
	kwargs = dict(alpha=0.6, bins=100, density= False, stacked=True)
	fig_size = (8,6)
	fig = Figure(figsize=fig_size)
	file_name = file_name
	ax = fig.add_subplot(111)
	ax.hist(x, **kwargs, color='g', label='Norm')
	ax.hist(y, **kwargs, color='r', label='Anomaly')
	title = os.path.basename(os.path.dirname(file_name))
	ax.set_title(title)
# 	ax.set_xlabel('Error')
	ax.set_xlabel('Mean of normalized pixel values')
	ax.set_ylabel('Frequency')
	ax.legend(['Norm', 'Anomaly'])
	ax.set_xlim([np.min(np.concatenate([x,y])), np.max(np.concatenate([x,y]))])
	canvas = FigureCanvasAgg(fig)
	canvas.print_figure(file_name, dpi=100)

def plot_AUC(file_name, auc_list):
	from matplotlib.backends.backend_agg import FigureCanvasAgg
	from matplotlib.figure import Figure
	fig_size = (8,6)
	fig = Figure(figsize=fig_size)
	file_name = file_name
	ax = fig.add_subplot(111)
	ax.plot(auc_list)
	title = os.path.basename(os.path.dirname(file_name))
	ax.set_title(title)
	ax.set_xlabel('Interations/100')
	ax.set_ylabel('AUC')
	ax.legend(['Detection'])
	ax.set_xlim([0,len(auc_list)])
	canvas = FigureCanvasAgg(fig)
	canvas.print_figure(file_name, dpi=100)

def save_recon_images(img_file_name, imgs, recons, errs, fig_size):
	from matplotlib.backends.backend_agg import FigureCanvasAgg
	from matplotlib.figure import Figure
	imgs, recons, errs = np.squeeze(imgs), np.squeeze(recons), np.squeeze(errs)
	test_size = imgs.shape[0]
	indx = np.random.randint(0,int(test_size/2))
	f, f_MP = imgs[indx,:,:], imgs[int(test_size/2)+indx,:,:]
	f_recon, f_MP_recon = recons[indx,:,:], recons[int(test_size/2)+indx,:,:]
	f_recon_err, f_MP_recon_err = errs[indx,:,:], errs[int(test_size/2)+indx,:,:]
# 	fig_size = (8,6)
	fig_size = fig_size
	fig = Figure(figsize=fig_size)
	rows, cols = 2, 3
	ax = fig.add_subplot(rows, cols, 1); cax=ax.imshow(f,cmap='gray'); fig.colorbar(cax); ax.set_title('Image'); ax.set_ylabel('f') 
	ax = fig.add_subplot(rows, cols, 2); cax=ax.imshow(f_recon,cmap='gray'); fig.colorbar(cax); ax.set_title('Recon');
	ax = fig.add_subplot(rows, cols, 3); cax=ax.imshow(f_recon_err,cmap='gray'); fig.colorbar(cax); ax.set_title('Error');
	ax = fig.add_subplot(rows, cols, 4); cax=ax.imshow(f_MP,cmap='gray'); fig.colorbar(cax); ax.set_ylabel('f_MP')
	ax = fig.add_subplot(rows, cols, 5); cax=ax.imshow(f_MP_recon,cmap='gray'); fig.colorbar(cax);
	ax = fig.add_subplot(rows, cols, 6); cax=ax.imshow(f_MP_recon_err,cmap='gray'); fig.colorbar(cax);
	canvas = FigureCanvasAgg(fig)
	canvas.print_figure(img_file_name, dpi=100)

def generate_folder(folder):
	if not os.path.exists(folder):
		os.system('mkdir -p {}'.format(folder))

# def get_parameters(model_name):
# 	splits = model_name.split('-')
# 	for i in range(len(splits)):
# 		if splits[i] == 'cn':
# 			nb_cnn = int(splits[i+1])
# 		elif splits[i] == 'fr':
# 			filters = int(splits[i+1])
# 		elif splits[i] == 'ks':
# 			kernel_size = int(splits[i+1])
# 		elif splits[i] == 'tr':
# 			train = int(splits[i+1][:2])* 1000
# 		elif splits[i] == 'vl':
# 			val = int(splits[i+1])
# 		elif splits[i] == 'test':
# 			test = int(splits[i+1])
# 		elif splits[i] == 'n':
# 			noise = float(splits[i+1])
# 	return nb_cnn, filters, kernel_size, train, val, test, noise

gpu = 0; docker = True
# noise = 0; version = 2
# train, val, test = 65000, 200, 200

os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu)

if docker:
	output_folder = '/data/results/MRI/'
else:
	output_folder = './data/MRI'

#model_name = 'AE2-MRI-cn-4-fr-32-ks-3-bn-True-skp-False-res-False-lr-0.0001-stps-200000-bz-50-tr-65k-vl-200-test-200-n-0.0'
#model_name = 'AE2-MRI-cn-4-fr-32-ks-3-bn-True-skp-False-res-False-lr-0.0001-stps-200000-bz-50-tr-65k-vl-200-test-200-n-40.0'
# model_name = 'AE1-MRI-cn-4-fr-32-ks-5-bn-True-skp-False-res-False-lr-0.0001-stps-300000-bz-50-tr-65k-vl-200-test-200-n-50.0'
model_name = 'f-AE2-MRI-cn-4-fr-32-ks-3-bn-True-skp-False-res-False-lr-0.0001-stps-200000-bz-50-tr-65k-vl-200-test-200-n-20.0-l-mse'
splits = model_name.split('-')
if len(splits[0])<=2:
	version =1
else:
	version = int(splits[0][2])
for i in range(len(splits)):
	if splits[i] == 'cn':
		nb_cnn = int(splits[i+1])
	elif splits[i] == 'fr':
		filters = int(splits[i+1])
	elif splits[i] == 'ks':
		kernel_size = int(splits[i+1])
	elif splits[i] == 'tr':
		train = int(splits[i+1][:2])* 1000
	elif splits[i] == 'vl':
		val = int(splits[i+1])
	elif splits[i] == 'test':
		test = int(splits[i+1])
	elif splits[i] == 'n':
		noise = float(splits[i+1])
	elif splits[i] == 'l':
		loss = splits[i+1]

model_folder = os.path.join(output_folder, model_name)

data_folder = output_folder+'/AE2-MRI-cn-6-fr-32-ks-3-bn-True-skp-False-res-False-lr-0.0001-stps-200000-bz-50-tr-65k-vl-200-test-200-n-40.0-l-correntropy'
X_SA_trn = np.load(data_folder + '/train.npy'); X_SA_val = np.load(data_folder +'/val.npy')
X_SA_tst = np.load(data_folder + '/test.npy'); X_SP_tst = np.load(data_folder + '/anomaly.npy')

# X_SA_trn, X_SA_val, X_SA_tst, X_SP_tst = load_MRI_true_data(docker = docker, train = train, val = val, normal = test, anomaly = test, noise = noise)
# X_SA_trn, X_SA_val, X_SA_tst, X_SP_tst = normalize_0_1(X_SA_trn), normalize_0_1(X_SA_val), normalize_0_1(X_SA_tst), normalize_0_1(X_SP_tst)
# padding into 128x128 pixels
# X_SA_trn, X_SA_val, X_SA_tst, X_SP_tst = pad_128(X_SA_trn), pad_128(X_SA_val), pad_128(X_SA_tst), pad_128(X_SP_tst)

## test data
Xt = np.concatenate([X_SA_tst, X_SP_tst], axis = 0)
yt = np.concatenate([np.zeros((len(X_SA_tst),1)), np.ones((len(X_SP_tst),1))], axis = 0).flatten()

## Dimension adjust
# X_SA_trn, X_SA_val, X_SA_tst, X_SP_tst, Xt = np.expand_dims(X_SA_trn, axis = 3), np.expand_dims(X_SA_val, axis = 3), np.expand_dims(X_SA_tst, axis = 3),\
# 		 np.expand_dims(X_SP_tst, axis = 3), np.expand_dims(Xt, axis = 3)

#nb_cnn = 4; 
batch_norm = True 
#filters = 32; kernel_size =3; 
scope = 'base'
x = tf.placeholder("float", shape=[None, 256, 256, 1])
if version == 1:
	h1, h2, y = auto_encoder(x, nb_cnn = nb_cnn, bn = batch_norm, filters = filters, kernel_size = [kernel_size, kernel_size], scope_name = scope)
elif version == 2:
	h1, h2, y = auto_encoder(x, nb_cnn = nb_cnn, bn = batch_norm, filters = filters, kernel_size = [kernel_size, kernel_size], scope_name = scope)
sqr_err = tf.square(y - x)
ssim_err = 1- tf.image.ssim(y, x, max_val = 1.0)
sigma = 0.1
err_correntropy = -tf.exp(-tf.square(x - y)/sigma)

# create a saver
vars_list = tf.trainable_variables(scope)
key_list = [v.name[:-2] for v in tf.trainable_variables(scope)]
key_direct = {}
for key, var in zip(key_list, vars_list):
	key_direct[key] = var
saver = tf.train.Saver(key_direct, max_to_keep=1)

# print out trainable parameters
for v in key_list:
	print_green(v)

continue_train = True
separate = True
# max_val, min_val = 100, 45
with tf.Session() as sess:
	tf.global_variables_initializer().run(session=sess)
	saver.restore(sess, model_folder+'/best')
	#saver.restore(sess, model_folder+'/best-184100')  # noise 50
	# saver.restore(sess, model_folder+'/best-170600')  # noise 40
	# saver.restore(sess, model_folder+'/best-192600')  # noise 0
	y_recon = y.eval(session = sess, feed_dict = {x:Xt})
	recon_means = np.squeeze(np.apply_over_axes(np.mean, y_recon, axes = [1,2,3]))
	recon_auc = roc_auc_score(yt, recon_means)
	print_yellow('AUC: Recon Mean {0:.4f}'.format(recon_auc))
	# separate calculation
	if separate:
		tst_errs = sqr_err.eval(session = sess, feed_dict = {x: X_SA_tst})
		anomaly_errs = sqr_err.eval(session = sess, feed_dict = {x: X_SP_tst})
# 		tst_errs = err_correntropy.eval(session = sess, feed_dict = {x: X_SA_tst})
# 		anomaly_errs = err_correntropy.eval(session = sess, feed_dict = {x: X_SP_tst})
		recon_errs = np.concatenate([tst_errs, anomaly_errs], axis = 0)
		recon_errs = np.apply_over_axes(np.mean, recon_errs, [1,2,3]).flatten()
		detect_auc = roc_auc_score(yt, recon_errs)
		print_green('Anomaly detection auc: {0:.4f}'.format(detect_auc))
		
	ssim_errs = ssim_err.eval(session = sess, feed_dict = {x:Xt})
	ssim_auc = roc_auc_score(yt, ssim_errs)
	print_yellow('AUC: SSIM {0:.4f}'.format(ssim_auc))
	tst_pixel_errs = sqr_err.eval(session = sess, feed_dict = {x:Xt})
	tst_pixel_errs1 = []
	max_val, min_val = np.max(tst_pixel_errs), np.min(tst_pixel_errs)
	for i in range(tst_pixel_errs.shape[0]):
		err = tst_pixel_errs[i,:]; err = (err -np.min(err))/(np.max(err)-np.min(err))*(max_val -min_val)+min_val 
		tst_pixel_errs1.append(err.reshape(1,256,256,1))
	tst_pixel_errs = np.concatenate(tst_pixel_errs1)
	img_means = np.squeeze(np.apply_over_axes(np.mean, Xt, axes = [1,2,3]))
	tst_img_errs = np.squeeze(np.apply_over_axes(np.mean, tst_pixel_errs, axes = [1,2,3]))
	test_auc = roc_auc_score(yt, tst_img_errs)
	mean_auc = roc_auc_score(yt, img_means)
	print_block(symbol = '-', nb_sybl = 50)
	print_yellow('AUC: AE {0:.4f} M: {1:.4f}'.format(test_auc, mean_auc))
	print(model_name)
	np.savetxt(os.path.join(model_folder,'AE_stat.txt'), tst_img_errs)
	np.savetxt(os.path.join(model_folder,'Pixel_mean_stat.txt'), img_means)
	np.savetxt(os.path.join(model_folder,'best_auc_n.txt'),[test_auc, mean_auc])
	hist_file = os.path.join(model_folder,'hist_n-{}.png'.format(model_name))
	plot_hist(hist_file, tst_img_errs[:int(len(tst_img_errs)/2)], tst_img_errs[int(len(tst_img_errs)/2):])
	plot_hist_pixels(model_folder+'/hist_mean_pixel.png'.format(model_name), img_means[:int(len(img_means)/2)], img_means[int(len(img_means)/2):])
	print_red('update best: {}'.format(model_name))
	saver.save(sess, model_folder +'/best')
	img_file_name = os.path.join(model_folder,'recon_n-{}.png'.format(model_name))
	save_recon_images(img_file_name, Xt, y_recon, tst_pixel_errs, fig_size = [11,5])
	
	if continue_train:
		recon_train = []
		batch_size = 50
		i = 0
# 		while(batch_size*i < X_SA_trn.shape[0]):
# 			if i % 100 == 0:
# 				print('{}-th batch'.format(i))
# 			batch_x = X_SA_trn[batch_size*i:min(batch_size*(i+1),X_SA_trn.shape[0])]
# 			recon_train.append(y.eval(session = sess, feed_dict = {x:batch_x}))
# 			i = i+1
		recon_val = y.eval(session = sess, feed_dict = {x:X_SA_val})
		recon_tst = y.eval(session = sess, feed_dict = {x:X_SA_tst})
		recon_anomaly = y.eval(session = sess, feed_dict = {x: X_SP_tst})
		generate_folder(model_folder + '/output_dataset')
		np.save(model_folder + '/train.npy', recon_train_arr)
		np.save(model_folder + '/val.npy', recon_val)
		np.save(model_folder +'/test.npy', recon_tst)
		np.save(model_folder + 'anomaly.npy', recon_anomaly)
	