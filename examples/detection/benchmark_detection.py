#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    TF-TRT Image classification benchmark.

    Copyright (c) 2019 Nobuo Tsukamoto

    This software is released under the MIT License.
    See the LICENSE file in the project root for more information.
"""

import argparse
import sys
import os
import time

import tensorflow as tf
from tensorflow.python.compiler.tensorrt import trt
# import tensorflow.contrib.tensorrt as trt

import numpy as np

from PIL import Image

def get_frozen_graph(graph_file):
    """Read Frozen Graph file from disk."""
    with tf.gfile.GFile(graph_file, "rb") as f:
        graph_def = tf.GraphDef()
        graph_def.ParseFromString(f.read())
    return graph_def

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', help='File path of tf-trt model.', required=True)
    parser.add_argument('--image', help='File path of image file.', required=True)
    parser.add_argument('--width', help='Input width.', required=True, type=int)
    parser.add_argument('--height', help='Input height.', required=True, type=int)
    parser.add_argument('--count', help='Repeat count.', default=100, type=int)
    args = parser.parse_args()

    tf.reset_default_graph()

    graph = get_frozen_graph(args.model)
    tf_config = tf.ConfigProto()
    tf_config.gpu_options.allow_growth = True
    tf_sess = tf.Session(config=tf_config)
    tf.import_graph_def(graph, name='')

    input_names = ['image_tensor']
    tf_input = tf_sess.graph.get_tensor_by_name(input_names[0] + ':0')
    tf_scores = tf_sess.graph.get_tensor_by_name('detection_scores:0')
    tf_boxes = tf_sess.graph.get_tensor_by_name('detection_boxes:0')
    tf_classes = tf_sess.graph.get_tensor_by_name('detection_classes:0')
    tf_num_detections = tf_sess.graph.get_tensor_by_name('num_detections:0')

    image = Image.open(args.image)

    width = args.width
    height = args.height

    image = np.array(image.resize((width, height)))

    times = []
    for i in range(args.count + 1):
        start_tm = time.time()
        scores, boxes, classes, num_detections = tf_sess.run([tf_scores, tf_boxes, tf_classes, tf_num_detections], feed_dict={
            tf_input: image[None, ...]
        })
        end_tm = time.time()

        if i > 0:
            times.append(end_tm - start_tm)
        else:
            print('First Inference : {0:.2f} ms'.format((end_tm - start_tm)* 1000))

    print('Inference : {0:.2f} ms'.format(np.array(times).mean() * 1000))

if __name__ == "__main__":
    main()
