# Copyright (c) Facebook, Inc. and its affiliates.

#!/bin/bash

DOMAIN=cartpole

SAVEDIR=./save

CUDA_VISIBLE_DEVICES=1 python train.py \
    env=${DOMAIN} \
    experiment=${DOMAIN} \
    agent=causal \
    seed=1