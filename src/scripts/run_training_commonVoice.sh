export TF_CUDNN_RESET_RND_GEN_STATE=1

python -u DeepSpeech.py \
   --n_hidden 2048 \
   --epochs 4 \
   --checkpoint_dir ~/DeepSpeechCommander/checkpoints \
   --train_files /media/necro/datasets/commonVoice/cv-corpus-5.1-2020-06-22/en/clips/train.csv \
   --dev_files /media/necro/datasets/commonVoice/cv-corpus-5.1-2020-06-22/en/clips/dev.csv \
   --test_files /media/necro/datasets/commonVoice/cv-corpus-5.1-2020-06-22/en/clips/test.csv \
   --train_batch_size 20 \
   --dev_batch_size 20 \
   --test_batch_size 20 \
   --dropout_rate 0.05 \
   --learning_rate 0.00001 \
   --train_cudnn true \
   --use_allow_growth true

#   --lm_alpha 0.75 \
#   --lm_beta 1.85 \
