'''
IR2 - Reproduction of "A Hierarchical Recurrent
      Encoder-Decoder for Generative Context-Aware Query Suggestion"
      by Sordoni et al.
Group 8

'''
import tensorflow as tf
import numpy as np
import layers
# import encoder
# import decoder
from encoder_grucell import Encoder
from decoder_grucell import Decoder


class HERED():
    """"
    This Class includes the methods to build de graph for the Recurrent
      Encoder-Decoder.
    """

    def __init__(self, vocab_size=50004, embedding_dim=300, query_dim=1000, session_dim=1500,
                 decoder_dim=1000, output_dim=50004, unk_symbol=0, eoq_symbol=1, eos_symbol=2, learning_rate=1e-1,
                 hidden_layer=1, batch_size=60):
        self.vocab_size = vocab_size
        self.batch_size = batch_size
        self.embedding_dim = embedding_dim
        self.query_dim = query_dim
        self.session_dim = session_dim
        self.decoder_dim = decoder_dim
        self.output_dim = output_dim
        self.unk_symbol = unk_symbol
        self.eoq_symbol = eoq_symbol
        self.eos_symbol = eos_symbol
        self.learning_rate = learning_rate
        self.hidden_layers = hidden_layer
        self.query_encoder = Encoder(batch_size=self.batch_size, level='query', num_hidden=self.query_dim)
        self.session_encoder = Encoder(batch_size=self.batch_size, level='session', input_dim=self.query_dim,
                                       num_hidden=self.session_dim)
        self.decoder_grucell = Decoder(input_dim=self.embedding_dim, num_hidden_query=self.query_dim,
                                       num_hidden_session=self.session_dim)
        self.vocabulary_matrix = tf.cast(tf.eye(self.vocab_size), tf.int32)

    def initialise(self, X):
        """
        Function to initialise the architecture. It runs until a session state is created.
        :param X: input data batch
        """

        # Create the embeddings
        embedder = layers.get_embedding_layer(vocabulary_size=self.vocab_size, embedding_dims=self.embedding_dim,
                                              data=X)
        # Create the query encoder state
        states = self.query_encoder.compute_state(x=embedder)
        # Create the session state
        self.initial_session_state = self.session_encoder.compute_state(x=self.initial_query_state)

        self.decoder_state = self.decoder_grucell.compute_state(x=self.initial_query_state,
                                                                session_state=self.initial_session_state)

    def inference(self, X, Y, sequence_max_length, attention=False):

        """
        Function to run the model.
        :param X: data batch [batch_size x max_seq]
        :param Y: target batch
        :param sequence_max_length: max_seq of the batch
        :return: logits [N, hidden size] where N is the number of words (including eoq) in the batch
        """

        with tf.variable_scope('X_embedder', reuse=tf.AUTO_REUSE):
            embedder = layers.get_embedding_layer(vocabulary_size=self.vocab_size,
                                                  embedding_dims=self.embedding_dim, data=X, scope='X_embedder')

        # For attention, pass bidirectional RNN
        if attention:
            with tf.variable_scope('gru_bidirectional', reuse=tf.AUTO_REUSE):
                self.annotations = layers.bidirectional_layer(embedder, self.query_dim, self.batch_size)
        # Create the query encoder state
        self.initial_query_state = self.query_encoder.compute_state(x=embedder)  # batch_size x query_dims
        # Create the session state
        self.initial_session_state = self.session_encoder.compute_state(
            x=self.initial_query_state)  # batch_size x session_dims
        # Create the initial decoder state
        self.initial_decoder_state = layers.decoder_initialise_layer(self.initial_session_state[0],
                                                                     self.decoder_dim)  # batch_size x decoder_dims

        # Run decoder and retrieve outputs and states for all timesteps
        self.decoder_outputs = self.decoder_grucell.compute_prediction(  # batch size x timesteps x output_size
            y=Y, state=self.initial_decoder_state, batch_size=self.batch_size, vocab_size=self.vocab_size)

        # For attention, calculate context vector
        if attention:
            self.context = layers.get_context_attention(self.annotations, self.decoder_outputs, self.decoder_dim,
                                                        self.query_dim, sequence_max_length,
                                                        self.batch_size)  # batch_size x max_steps
            # Concatenate context vector to decoder state, assuming in a GRU states = outputs
            self.decoder_states_attention = tf.concat([self.decoder_outputs, tf.expand_dims(self.context, 2)],
                                                      axis=2)  # TODO: check this
            # Calculate the omega function w(d_n-1, w_n-1) for attention
            with tf.variable_scope('output_layer', reuse=tf.AUTO_REUSE):
                omega = layers.output_layer(embedding_dims=self.embedding_dim, vocabulary_size=self.vocab_size,
                                            num_hidden=self.decoder_dim + 1,
                                            state=self.decoder_states_attention, word=Y)
        else:
            with tf.variable_scope('output_layer', reuse=tf.AUTO_REUSE):
                omega = layers.output_layer(embedding_dims=self.embedding_dim, vocabulary_size=self.vocab_size,
                                            num_hidden=self.decoder_dim,
                                            state=self.decoder_outputs, word=Y)

        # Get embeddings for decoder output

        with tf.variable_scope('ov_embedder', reuse=tf.AUTO_REUSE):
            ov_embedder = tf.get_variable(name='Ov_embedder', shape=[self.vocab_size, self.embedding_dim],
                                          initializer=tf.random_normal_initializer(mean=0.0, stddev=1.0))

        # Dot product between omega and embeddings of vocabulary matrix
        logits = tf.einsum('bse,ve->bsv', omega, ov_embedder)

        return logits

    def get_predictions(self, X, previous_word=None, attention=False, state=None, sequence_max_length=1):

        """
        Function to run the model.
        :param X: data batch [batch_size x max_seq]
        :param Y: target batch
        :param sequence_max_length: max_seq of the batch
        :return: logits [N, hidden size] where N is the number of words (including eoq) in the batch
        """
        with tf.variable_scope('X_embedder', reuse=tf.AUTO_REUSE):
            embedder = layers.get_embedding_layer(vocabulary_size=self.vocab_size,
                                                  embedding_dims=self.embedding_dim, data=X, scope='X_embedder')

        # For attention, pass bidirectional RNN
        if attention:
            with tf.variable_scope('gru_bidirectional', reuse=tf.AUTO_REUSE):
                self.annotations = layers.bidirectional_layer(embedder, self.query_dim, self.batch_size)
        # Create the query encoder state
        self.initial_query_state = self.query_encoder.compute_state(x=embedder)  # batch_size x query_dims
        # Create the session state
        self.initial_session_state = self.session_encoder.compute_state(
            x=self.initial_query_state)  # batch_size x session_dims
        # Create the initial decoder state
        self.initial_decoder_state = layers.decoder_initialise_layer(self.initial_session_state[0],
                                                                     self.decoder_dim)  # batch_size x decoder_dims
        if state is None:
            previous_word = tf.zeros([self.batch_size, 1, self.vocab_size])
            state = self.initial_decoder_state
        # Run decoder and retrieve outputs for next words
        self.decoder_outputs, state = self.decoder_grucell.compute_one_prediction(  # batch size x 1 x output_size
            y=previous_word, state=state, batch_size=self.batch_size, vocab_size=self.vocab_size)

        # For attention, calculate context vector
        if attention:
            self.context = layers.get_context_attention(self.annotations, self.decoder_outputs, self.decoder_dim,
                                                        self.query_dim, sequence_max_length,
                                                        self.batch_size)  # batch_size x max_steps
            # Concatenate context vector to decoder state, assuming in a GRU states = outputs
            self.decoder_states_attention = tf.concat([self.decoder_outputs, tf.expand_dims(self.context, 2)],
                                                      axis=2)  # TODO: check this
            # Calculate the omega function w(d_n-1, w_n-1) for attention
            with tf.variable_scope('output_layer', reuse=tf.AUTO_REUSE):
                omega = layers.output_layer(embedding_dims=self.embedding_dim, vocabulary_size=self.vocab_size,
                                            num_hidden=self.decoder_dim + 1,
                                            state=self.decoder_states_attention, word=tf.argmax(previous_word, 2))
        else:
            with tf.variable_scope('output_layer', reuse=tf.AUTO_REUSE):
                omega = layers.output_layer(embedding_dims=self.embedding_dim, vocabulary_size=self.vocab_size,
                                            num_hidden=self.decoder_dim,
                                            state=self.decoder_outputs, word=tf.argmax(previous_word, 2))

        with tf.variable_scope('ov_embedder', reuse=tf.AUTO_REUSE):
            ov_embedder = tf.get_variable(name='Ov_embedder', shape=[self.vocab_size, self.embedding_dim],
                                          initializer=tf.random_normal_initializer(mean=0.0, stddev=1.0))

        logits = tf.einsum('bse,ve->bsv', omega, ov_embedder)

        return logits, state

    def validation(self, X, Y, sequence_max_length=1, attention=False):

        x_list = tf.unstack(X, axis=1)
        result, state = self.get_predictions(tf.expand_dims(x_list[0], 1), attention=attention)
        outputs = result
        for i in range(1, len(x_list)):
            result, state = self.get_predictions(X=tf.expand_dims(x_list[i], 1), previous_word=result, state=state,
                                                 attention=attention)
            outputs = tf.concat([outputs, result], 1)
        predictions = tf.argmax(outputs, 2)
        return predictions  # predictions

    def predictions(self, X, Y, sequence_max_length=1, attention=False):

        x_list = tf.unstack(X, axis=1)
        result, state = self.get_predictions(tf.expand_dims(x_list[0], 1), attention=attention)
        outputs = result
        for i in range(1, len(x_list)):
            result, state = self.get_predictions(X=tf.expand_dims(x_list[i], 1), previous_word=result, state=state,
                                                 attention=attention)
            outputs = tf.concat([outputs, result], 1)
        predictions = tf.argmax(outputs, 2)
        return outputs  # predictions

    def get_length(self, sequence):
        used = tf.sign(tf.reduce_max(tf.abs(sequence), 1))
        # length = tf.reduce_sum(used, 0)
        length = tf.cast(used, tf.int32)
        return length

    def get_loss(self, logits, labels):
        # same as for train_step.....
        mask = tf.sign(tf.abs(tf.convert_to_tensor(labels)))
        loss = tf.reduce_sum(tf.losses.sparse_softmax_cross_entropy(logits=logits, labels=labels, weights=mask))
        # loss =tf.reduce_sum(tf.log(tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=labels)))

        tf.summary.scalar('LOSS', loss)
        return loss

    def other_loss(self, logits, labels):
        # Compute cross entropy for each frame.
        l = tf.log(logits)
        labels_one_hot = tf.one_hot(labels, self.vocab_size)
        cross_entropy = labels_one_hot * l
        cross_entropy = -tf.reduce_sum(cross_entropy, 2)
        mask = tf.sign(tf.reduce_max(tf.abs(labels_one_hot), 2))
        cross_entropy *= mask
        # Average over actual sequence lengths.
        cross_entropy = tf.reduce_sum(cross_entropy, 1)
        cross_entropy /= tf.reduce_sum(mask, 1)
        return tf.reduce_mean(cross_entropy)
