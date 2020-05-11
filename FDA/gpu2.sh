# python AE.py --gpu 2 --cn 4 --fr 32 --ks 5 --bn True --lr 1e-4 --step 100000 --bz 50 --train 65000 --val 400 --test 400 --noise 5
# python AE.py --gpu 2 --cn 4 --fr 32 --ks 3 --bn True --lr 1e-4 --step 200000 --bz 50 --train 65000 --val 200 --test 200 --noise 20 --version 2
python AE_ssim.py --gpu 2 --cn 8 --fr 32 --ks 3 --bn True --lr 1e-3 --step 300000 --bz 50 --train 7100 --val 200 --test 200 --version 2 --dataset dense --loss ssim