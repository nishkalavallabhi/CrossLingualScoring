#!/usr/bin/python3

from __future__ import print_function
import numpy as np
np.random.seed(1337)  # for reproducibility

from keras.preprocessing import sequence
from keras.models import Sequential, Model
from keras.layers import Dense, Flatten, Dropout, Activation, Input, merge
from keras.layers import Embedding, Convolution1D, MaxPooling1D
from keras.layers import AveragePooling1D, LSTM, GRU
from keras.utils import np_utils
import sys, time, re
from collections import defaultdict
from gensim.utils import simple_preprocess

_white_spaces = re.compile(r"\s\s+")
maxlen = 512
embedding_dims = 16
batch_size = 128
nb_epoch = 40
nb_filter = 50
filter_length = 5
pool_length = 5
minwordfreq = 15
mincharfreq = 0
maxwordlen = 400

tokenizer_re = re.compile("\w+|\S")


data_path = "../data"

def read_data():
    labels = []
    lg_labels = []
    documents = []
    for data_file in glob.iglob(sys.argv[1]+"/*/*"):
        if "parsed" in data_file: continue
        doc = open(data_file, "r").read().strip()
        wrds = doc.split(" ")
        lang_label = data_file.split("/")[-2]
        label = data_file.split("/")[-1].split(".txt")[0].split("_")[-1]
        if label == "EMPTY": continue
        if len(wrds) >= maxwordlen:
            doc = " ".join(wrds[:maxwordlen])
        doc = _white_spaces.sub(" ", doc)
        labels.append(label)
        lg_labels.append(lang_label
        documents.append(doc)
        
    return (documents, labels, lg_labels)

def char_tokenizer(s):
    return list(s)

def word_tokenizer(s):
    return tokenizer_re.findall(s)

def getWords(D):
    wordSet = defaultdict(int)
    max_features = 3
    for d in D:
        for c in word_tokenizer(d):
            wordSet[c] += 1
    for c in wordSet:
        if wordSet[c] > minwordfreq:
            max_features += 1
    return wordSet, max_features

def getChars(D):
    charSet = defaultdict(int)
    max_features = 3
    for d in D:
        for c in char_tokenizer(d):
            charSet[c] += 1
    for c in charSet:
        if charSet[c] > mincharfreq:
            max_features += 1
    return charSet, max_features

def transform(D, vocab, minfreq, tokenizer="char"):
    features = defaultdict(int)
    count = 0
    for i, k in enumerate(vocab.keys()):
        if vocab[k] > minfreq:
            features[k] = count
            count += 1
    
    start_char = 1
    oov_char = 2
    index_from = 3
    
    X = []
    for j, d in enumerate(D):
        x = [start_char]
        z = None
        if tokenizer == "word":
            z = word_tokenizer(d)
        else:
            z = char_tokenizer(d)
        for c in z:
            freq = vocab[c]
            if c in vocab:
                if c in features:
                    x.append(features[c]+index_from)
                else:
                    x.append(oov_char)
            else:
                continue
        X.append(x)
    return X

    
print("Reading the training set... ", end="")
sys.stdout.flush()
pt = time.time()
doc_train, y_lang_labels, y_labels = read_data()
print(time.time() - pt)

print("Transforming the datasets... ", end="")
sys.stdout.flush()
pt = time.time()
word_vocab, max_word_features = getWords(doc_train)
char_vocab, max_char_features = getChars(doc_train)
print("Number of word features= ", max_word_features, " char features= ", max_char_features)
x_char_train = transform(doc_train, char_vocab, mincharfreq, tokenizer="char")
x_word_train = transform(doc_train, word_vocab, minwordfreq, tokenizer="word")
print(len(x_char_train), 'train sequences')
print(time.time() - pt)

print('Pad sequences (samples x time)')
x_char_train = sequence.pad_sequences(x_char_train, maxlen=maxlen)
x_word_train = sequence.pad_sequences(x_word_train, maxlen=maxwordlen)
print('x_train shape:', x_char_train.shape)

print("Transforming the labels... ", end="")
sys.stdout.flush()
pt = time.time()
unique_labels = list(set(y_labels))
lang_labels = ["CZ", "IT", "DE"]
print("Class labels = ",unique_labels)
n_classes = len(unique_labels)
n_grp_classes = len(group_labels)

grp_train, grp_test = [], []

y_train = [unique_labels.index(y) for y in y_labels]
lng_train = [group_labels.index(y) for y in y_lang_labels]

y_train = np_utils.to_categorical(np.array(y_train), len(unique_labels))
lng_train = np_utils.to_categorical(np.array(y_train), len(lang_labels))

print(time.time() - pt)

cv_accs, cv_f1 = [], []
k_fold = StratifiedKFold(10)

for train, test in k_fold.split(x_word_train, y_labels):
    print('Build model...')
    char_input = Input(shape=(maxlen, ), dtype='int32', name='char_input')
    charx = Embedding(max_char_features, 16, input_length=maxlen,
            dropout=0.25)(char_input)

    word_input = Input(shape=(maxwordlen, ), dtype='int32', name='word_input')
    wordx = Embedding(max_word_features, 32, input_length=maxwordlen,
        dropout=0.25)(word_input)

    #charx = Convolution1D(nb_filter=128, filter_length=9, activation="relu")(charx)
    #charx = MaxPooling1D(pool_length=maxlen-6)(charx)#Or Max-pooling
    #charx = GRU(embedding_dims, dropout_W=0.2, dropout_U=0.2, return_sequences=True)(charx)
    #charx = AveragePooling1D(pool_length=maxlen)(charx)
    charx = Flatten()(charx)
    #charx = Dense(160, activation="relu")(charx)
    #charx = Dropout(0.25)(charx)

    #wordx = Convolution1D(nb_filter=128, filter_length=2)(wordx)
    #wordx = Convolution1D(nb_filter=256, filter_length=2, activation="relu")(wordx)
    #wordx = GRU(128, dropout_W=0.25, dropout_U=0.25, return_sequences=True)(wordx)
    #wordx = AveragePooling1D(pool_length=maxwordlen)(wordx)#Or Max-pooling
    #wordx = MaxPooling1D(pool_length=2)(wordx)#Or Max-pooling
    #wordx1 = LSTM(32)(wordx)
    #wordx2 = LSTM(32, go_backwards=True)(wordx)
    #wordx = AveragePooling1D(pool_length=4)(wordx)#Or Max-pooling
    wordx = Flatten()(wordx)
    #wordx = Dense(256, activation="relu")(wordx)
    #wordx = Dropout(0.25)(wordx)

    y = merge([charx, wordx], mode='concat')
    grp_predictions = Dense(n_grp_classes, activation='softmax')(y)
    #grp_predictions1 = Dense(32, activation='relu')(grp_predictions)
    y = merge([y, grp_predictions], mode='concat')
    #y = Dense(20, activation="relu")(y)

    #y = Dense(50, activation='relu', name='hidden_layer')(y)
    y = Dropout(0.25)(y)
    y_predictions = Dense(n_classes, activation='softmax')(y)

    model = Model(input=[char_input, word_input], output=[y_predictions, grp_predictions])

    model.summary()
    model.compile(loss='categorical_crossentropy',
              optimizer='adadelta',
              metrics=['accuracy'])#, loss_weights=[1.0, 0.5])

    hist = model.fit([x_char_train[train], x_word_train[train]], [y_train[train], lng_train[train]],
              batch_size=batch_size,
              nb_epoch=nb_epoch,
              validation_data=([x_char_train[test], x_word_train[test]], [y_train[test], lng_train[test]]))
    
    print("All done!\n{}".format(hist.history), file=sys.stderr)


