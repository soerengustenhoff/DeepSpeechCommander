export TF_CUDNN_RESET_RND_GEN_STATE=1

python -u DeepSpeech.py \
   --n_hidden 2048 \
   --epochs 1 \
   --checkpoint_dir ~/DeepSpeechCommander/checkpoints \
   --train_files ~/datasets/voxforge/voxforge-train.csv \
   --dev_files ~/datasets/voxforge/voxforge-dev.csv \
   --test_files ~/datasets/voxforge/voxforge-test.csv \
   --train_batch_size 24 \
   --dev_batch_size 24 \
   --test_batch_size 24 \
   --dropout_rate 0.05 \
   --learning_rate 0.0001 \
   --train_cudnn true \
   --use_allow_growth true

#   --lm_alpha 0.75 \
#   --lm_beta 1.85 \
