import _pickle as cPickle
import numpy as np
train_file = 'allq_train.p'
valid_file = 'allq_valid.p'

# random_list = range(0,1000,50)
# element = 0

# uses data/new_new_batch/*
def get_batch_new(random_list, data, eoq, type='train', element=50, batch_size=50, max_len=50):

    """
    Function to get a batch from element. It pads it to max_len and add the eoq symbol.
    :param random_list: list of queries
    :param data: data to get batches from
    :param eoq: end of query symbol
    :param type: type of data
    :param element: element from which start the batch
    :param batch_size: batch size
    :param max_len: max sequence length
    :return: x_batch, y_batch, batch_max_len, random_list
    """

    if type == 'train':

        random_list.remove(element)
        train_list = data[element]
        batch_max_len = max_len

        padded_train = []
        for i in train_list:
            listofzeros = [0] * batch_max_len
            listofzeros[:len(i)] = i
            listofzeros = listofzeros[0:max_len]
            if len(i)<max_len:
                listofzeros[len(i)] = eoq
            else:
                listofzeros[max_len-1] = eoq
            padded_train.append(listofzeros)
        full_batch = np.asarray(padded_train)
        y_batch = full_batch[1:]
        x_batch = full_batch[:-1]

        return x_batch, y_batch, batch_max_len, random_list



# uses data/new_batch/*
def get_batch(random_list, data, eoq, type='train', element=50, batch_size=50, max_len=50):

    """
    Function to get a batch from element. It pads it to max_len and add the eoq symbol.
    :param random_list: list of queries
    :param data: data to get batches from
    :param eoq: end of query symbol
    :param type: type of data
    :param element: element from which start the batch
    :param batch_size: batch size
    :param max_len: max sequence length
    :return: x_batch, y_batch, batch_max_len, random_list
    """

    if type == 'train':

        random_list.remove(element)
        train_list = []
        for i in range(element, element+batch_size+1):
            train_list.append(data[i])
        batch_max_len = max_len

        '''
        batch_max_len = 0
        for i in train_list:
            curlen =len(i)
            if curlen>batch_max_len:
                batch_max_len=curlen
        if batch_max_len>max_len:
            batch_max_len=max_len#'''

        padded_train = []
        for i in train_list:
            listofzeros = [0] * batch_max_len
            listofzeros[:len(i)] = i
            listofzeros = listofzeros[0:max_len]
            if len(i)<max_len:
                listofzeros[len(i)] = eoq
            else:
                listofzeros[max_len-1] = eoq
            padded_train.append(listofzeros)
        full_batch = np.asarray(padded_train)
        y_batch = full_batch[1:]
        x_batch = full_batch[:-1]

        return x_batch, y_batch, batch_max_len, random_list




