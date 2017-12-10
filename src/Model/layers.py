"""
IR2 - Reproduction of "A Hierarchical Recurrent
      Encoder-Decoder for Generative Context-Aware Query Suggestion"
      by Sordoni et al.
Group 8

File to implement the methods that describe each layer needed for the model.

"""

import tensorflow as tf
import numpy as np


def get_embedding_layer(vocabulary_size, embedding_dims, data, scope):
    """
    Layer to train embeddings and retunr the embeddings for data
    :param vocabulary_size: int for the vocabulary size
    :param embedding_dims: int for the embedding space dimensions
    :param data: tensor with the data to obtain the embeddings from
    :return: embeddings for data

    """
    with tf.variable_scope(scope):
        embeddings_weights = tf.get_variable(name=scope, shape=[vocabulary_size, embedding_dims],
                                             initializer=tf.random_normal_initializer(mean=0.0, stddev=1.0))
        word_embeddings = tf.nn.embedding_lookup(embeddings_weights, data)

        return word_embeddings


def output_layer(embedding_dims, num_hidden, vocabulary_size, state, word):
    """
    Layer to get the output to predict the probability of the next word (word_t+1).
    The previous recurrent state of the decoder and the previous word are used.

    :param embedding_dims: int, dimensions of the embeddings vector
    :param num_hidden: int, query-level dimensionality
    :param vocabulary_size: int, vocab_size
    :param state: previous state of the encoder, should be flatten
    :param word: 1D tensor embedding, previous word, should be flatten
    :return:
    """
    with tf.variable_scope('output_layer'):
        # Define the weights H_o, E_o and bias b_o
        H_ouput = tf.get_variable(name='h_output', shape=[embedding_dims, num_hidden],
                                  initializer=tf.random_normal_initializer(mean=0.0, stddev=1.0))
        E_output = tf.get_variable(name='e_output', shape=[embedding_dims, vocabulary_size],
                                   initializer=tf.random_normal_initializer(mean=0.0,stddev=1.0))
        b_output = tf.get_variable(name='b_output', shape=[embedding_dims],
                                   initializer=tf.truncated_normal_initializer(mean=0.0, stddev=1.0))

        y_one_hot = tf.one_hot(word, vocabulary_size)
        start_word = tf.expand_dims(tf.zeros([tf.shape(word)[0],vocabulary_size]),1)
        # y_one_hot_shifted = tf.concat([start_word,y_one_hot],1)
        #y_embedding_onehot = get_embedding_layer(vocabulary_size=vocabulary_size,
        #                                         embedding_dims=embedding_dims, scope='output_embedding', data=y_one_hot_shifted)

        #return tf.matmul(state, tf.transpose(H_ouput)) + tf.transpose(tf.cast(y_embedding_onehot, tf.float32)) + b_output
        # tf.einsum('bsh,eh->bse',state, H_ouput)
        # tf.einsum('bsv,ev->bse',y_one_hot, E_output)
        print('state,one hot')
        print(state)
        print(y_one_hot)
        return tf.einsum('bsh,eh->bse',state, H_ouput) + tf.einsum('bsv,ev->bse',y_one_hot, E_output) + b_output


def decoder_initialise_layer(initial_session_state, hidden_dims):
    """
    Function to train the weights for the decoder init state d = tanh(D_0 * s_{m-1} + b_0

    :param initial_session_state: initial session state to initialise the decoder
    :param hidden_dims: the hidden dimensions of the RNN
    :return: returns the fully connected layer used to initialise the decoder
    """

    with tf.variable_scope('decoder_initial_layer', reuse=tf.AUTO_REUSE):
        return tf.contrib.layers.fully_connected(initial_session_state, hidden_dims, activation_fn=tf.nn.tanh,
                                                 weights_initializer=tf.contrib.layers.xavier_initializer(),
                                                 biases_initializer=tf.zeros_initializer())


def get_context_attention(annotations, decoder_states, decoder_dims, encoder_dims):
    """
    Fully connected layer to calculate the attention scores (alignment model). Calculates attention for a batch and for
    step (word level) for a current hidden state of the decoder.

    :param annotations: (batch_size x max_steps x (2 x enc_dims)), annotations from bidirectional RNN
    :param decoder_states: (batch_size x max_Steps xdec_dims), current hidden state of the decoder for which calculate attention.
    :param decoder_dims: decoder dims
    :param encoder_dims: encoder dims
    :return: (batch_size, max_steps) context vector with attention scores
    """

    # Define weight for attention
    w = tf.get_variable(name='weight', shape=(2 * encoder_dims, decoder_dims),
                        initializer=tf.random_normal_initializer(stddev=0.01))
    # Calculate alphas for the context vector
    alphas = tf.nn.softmax(tf.einsum('bme, ebm -> bm', annotations, tf.einsum('ed, bmd -> ebm', w, decoder_states)))  # batch_size x seq_leght
    # Calculate context vector
    context = tf.reduce_sum(tf.einsum('bm, bme -> bme', alphas, annotations), axis=2) # reduce over 2 x enc_dims

    return context


def bidirectional_layer(x, encoder_dims, batch_size, embedding_dims):
    """
    Calculate annotations for attention with a bidirectional RNN
    :param x: batch x seq_length x word_embedding
    :param encoder_dims: query_level encoder dims
    :param batch_size: batch size
    :return: concatenated hidden states from the forward and backward pass: batch_size x seq_lenght x (2 x encoder_dims)
    """
    initializer_weights = tf.variance_scaling_initializer()  # xavier
    initializer_biases = tf.constant_initializer(0.0)

    gru_cell = tf.contrib.rnn.GRUCell(encoder_dims, kernel_initializer=initializer_weights,
                                      bias_initializer=initializer_biases)
    x_length = length(tf.convert_to_tensor(x))

    # TODO: x should be a list seq_length x batch_size x embedding

    a = tf.unstack(x, axis=1)

    x_reverse = tf.reverse(x, axis=[1])
    x_reverse_unstack = tf.unstack(x_reverse, axis=1)
    # print(x_reverse)
    # print(x_reverse_unstack)
    # print(len(x_reverse_unstack))

    # Forward pass
    _, states_forward = tf.nn.static_rnn(
        gru_cell,
        a,
        dtype=tf.float32,
        sequence_length=x_length,
        initial_state=gru_cell.zero_state([batch_size], tf.float32))

    print(states_forward)

    # Backward pass
    _, states_backward = tf.nn.static_rnn(
        gru_cell,
        x_reverse_unstack,
        dtype=tf.float32,
        sequence_length=x_length,
        initial_state=gru_cell.zero_state([batch_size], tf.float32))

    print(states_backward)
    # TODO: we need all states....
    return tf.concat([states_forward, states_backward], axis=2)


def length(sequence):
    """
     :sequence: batch of padded length; with zero vectors after eoq_symbol
     :return:   vector determining length of queries (at what point the eoq_symbol is encountered)
    """
    used = tf.sign(tf.reduce_max(tf.abs(tf.convert_to_tensor(sequence)), 2))
    length = tf.reduce_sum(used, 1)
    length = tf.cast(length, tf.int32)
    return length