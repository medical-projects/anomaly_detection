# python noiseAE.py --gpu 2 --cn 4 --fr 32 --ks 5 --bn True --lr 1e-4 --step 200000 --bz 50 --train 65000 --val 200 --test 200 --noise_level 15 --us_factor 4 --version 
# python AE_train.py --gpu 2 --cn 5 --fr 32 --ks 5 --bn False --lr 1e-4 --step 100000 --bz 50 --version 4 --train 65000 --val 400 --test 1000
# python AE_labels.py --gpu 2 --cn 4 --fr 32 --ks 5 --bn True --lr 1e-4 --step 100000 --bz 50 --version 1 --train 65000 --val 400 --test 1000 --loss mae --ano_weight 0.01
python AE_labels.py --gpu 2 --cn 4 --fr 32 --ks 5 --bn True --lr 5e-6 --step 100000 --bz 40 --version 1 --train 65000 --val 400 --test 1000 --loss mae --ano_weight 0.01 --anomaly 4x