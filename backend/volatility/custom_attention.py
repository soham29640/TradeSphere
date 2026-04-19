import tensorflow as tf
from tensorflow.keras.layers import Layer

class AttentionSum(Layer):
    def call(self, inputs):
        attention, lstm_output = inputs
        return tf.reduce_sum(attention * lstm_output, axis=1)
