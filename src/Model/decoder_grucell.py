"""
IR2 - Reproduction of "A Hierarchical Recurrent
      Encoder-Decoder for Generative Context-Aware Query Suggestion"
      by Sordoni et al.
Group 8

"""

import tensorflow as tf
import numpy as np

class Decoder(object):

    def __init__(self,batch_size, reuse, input_dim=300, num_hidden_query=1000, num_hidden_session=1500):
        """
        This Class implements a Decoder.

        :param batch_size: int, length of batch
        :param reuse: bool, parameter to reuse tensorflow variables
        :param input_dim: int, word embedding dimensions
        :param num_hidden_query: int, dimensions for the hidden state of the decoder, same as the query_encoder
        :param num_hidden_session: int, dimensions for the hidden state of the session enconder
        """
        self.input_dim = input_dim
        self.num_hidden_query = num_hidden_query
        self.num_hidden_session = num_hidden_session
        self.reuse = reuse
        self.batch_size = batch_size

        initializer_weights = tf.variance_scaling_initializer() #xavier
        initializer_biases = tf.constant_initializer(0.0)

        self.gru_cell = tf.contrib.rnn.GRUCell(num_hidden, kernel_initializer=initializer_weights, bias_initializer=initializer_biases)
        # Weights for initial recurrent state
        self.Bo = tf.get_variable(shape= [self.num_hidden_query], initializer= initializer_biases, name= 'Bo')
        self.Do = tf.get_variable(shape= [self.num_hidden_query, self.num_hidden_session], initializer= initializer_biases, name= 'Do' )

    def compute_state(self, x, session_state, query_length):
        """
        :session_state: state to initialise the recurrent state of the decoder
        :x: array of embeddings of query batch
        :return: query representation tensor
        """
        # Initialise recurrent state with session_state
        state = tf.tanh(tf.sum(tf.matmul(session_state, self.Do), self.Bo))
        # Calculate RNN states
        for step in range(query_length):
            _, state = self.gru_cell(x[step], state)

        return state

    def compute_prediction(self, session_state, eoq_symbol):
        # is output of decoder a vector of size=vocab_size (all 0s except the value corresponding to the word),
        #or an embedding (and then we look for the word with the closest embedding)?
        state = tf.tanh(tf.sum(tf.matmul(session_state, self.Do), self.Bo))
        # Calculate RNN states
        outputs = []
        output  = self.gru_cell(state)
        output  = self.prediction(state)
        stop_after_ten_words = 10
        
        while calculate_word(output) != eoq_symbol and stop_after_ten_words>0:
            output, state = self.gru_cell(output, state)
            output        = self.prediction(output)
            outputs.append(output)
            stop_after_ten_words -= 1

    def calculate_word(self, gru_output):
        # Calculate word given the output of the Decoder 
        raise BaseException('Not implemented')

    def prediction(self, gru_output):
        # Transform output to prediction given the output of the Decoder
        raise BaseException('Not implemented')
