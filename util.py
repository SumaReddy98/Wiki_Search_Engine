import re
import os
import heapq
import string
import Stemmer
from stop_words import get_stop_words
from math import log10

def get_word(line):
    '''
    line has 'word:posting_list' format and we need to extract the word
    '''
    word = ''
    for ch in line:
        if (ch == ':'):
            break
        word += ch

    return word


def extract_data_posting(posting):
    '''
    Gets the doc_id value and tf-idf value
    from the posting of the form <id>,<tf-idf>(<char><freq>)+

    @param posting : C{Str}
    '''

    obj = posting.split(',')
    doc_id = int(obj[0])
    for i in range(len(obj[1])):
        if ord(obj[1][i]) > 96 and ord(obj[1][i]) < 123:
            break

    tfidf_value = float(obj[1][:i])

    return doc_id, tfidf_value


def get_tf_value(posting):
    '''
    Returns the tf_value for a posting list
    Any posting is of the form <id>(<character><number>)+

    @param posting : C{str}
    @return : C{int}
    '''
    weight = {'t' : 2, 'b' : 1.5, 'c': 0.75, 'i' : 1.5, 'r' : 0.5, 'e' : 0.5}

    overall_freq = 0

    obj = posting.split('r')
    if len(obj) == 2:
        overall_freq += weight['r'] * int(obj[1])

    obj = obj[0].split('e')
    if len(obj) == 2:
        overall_freq += weight['e'] * int(obj[1])

    obj = obj[0].split('c')
    if len(obj) == 2:
        overall_freq += weight['c'] * int(obj[1])

    obj = obj[0].split('i')
    if len(obj) == 2:
        overall_freq += weight['i'] * int(obj[1])

    obj = obj[0].split('b')
    if len(obj) == 2:
        overall_freq += weight['b'] * int(obj[1])

    obj = obj[0].split('t')
    if len(obj) == 2:
        overall_freq += weight['t'] * int(obj[1])

    tf = log10(1 + overall_freq)

    return tf


def add_tfidf_value_posting(posting, tfidf_value):
    '''
    Any posting is of the form <id>(<character><number>)+
    Returns <id>,<ifidf_value>(<character><number>)+
    We also return the doc_id value so that we can sort based on that and
    merging the posting lists would be easier at query time
    '''

    # Finding the index just after the doc id ends
    for i in range(len(posting)):
        if not posting[i].isdigit():
            break

    doc_id = int(posting[:i])
    modified_posting = str(doc_id) + ',' + str(tfidf_value) + posting[i:]

    return (doc_id, modified_posting)


def get_champions_list(posting_list, total_number_documents, num_champions):
    '''
    This function takes the posting list for a term and for each posting
    adds the tf-idf value.
    num_champions denotes the maximum number of docs in the champion list

    @param posting_list : C{str}
    @return : C{str} representing the tfidf added posting list
    '''

    postings = posting_list.split('|')
    idf_value = log10(total_number_documents) - log10(len(postings))

    for i in range(len(postings)):
        tf_value = get_tf_value(postings[i])
        tfidf_value = round(tf_value * idf_value, 2)
        # Multiplying by -1 as there is no max heap in python
        postings[i] = (-1 * tfidf_value, postings[i])

    # Modified postings have the tfidf value present as part of posting
    modified_postings = []
    heapq.heapify(postings)
    for i in range(min(num_champions, len(postings))):
        posting_obj = heapq.heappop(postings)
        tfidf_value = posting_obj[0] * -1
        posting = posting_obj[1]
        modified_posting_obj = add_tfidf_value_posting(posting, tfidf_value)
        modified_postings.append(modified_posting_obj)

    # Below will make the champion list sort by the doc_id (As in tuple first entry is doc_id)
    modified_postings.sort()
    for i in range(len(modified_postings)):
        modified_postings[i] = modified_postings[i][1]
    modified_postings = '|'.join(modified_postings)

    return modified_postings


def get_tfidf_added_list(posting_list, total_number_documents):
    '''
    This function adds the tfidf value to each posting of the posting list
    '''
    postings = posting_list.split('|')
    idf_value = log10(total_number_documents) - log10(len(postings))

    for i in range(len(postings)):
        tf_value = get_tf_value(postings[i])
        tfidf_value = round(tf_value * idf_value, 2)
        postings[i] = add_tfidf_value_posting(postings[i], tfidf_value)[1]

    modified_postings = '|'.join(postings)
    return modified_postings


def parse_secondary_index(secondary_index_fp):
    '''
    0 : 0,304038
    1 : 304060,3081208
    2 : 3081227,3925411
    3 : 3925430,4339464
    4 : 4339484,4688569
    5 : 4688588,5023804
    6 : 5023823,5305081 .....
    '''

    # Need to parse above format
    secondary_index_dict = {}
    lines = secondary_index_fp.readlines()
    for line in lines:
        line = line.strip()
        obj = line.split(' : ')
        obj1 = obj[1].split(',')
        start_pos = int(obj1[0])
        end_pos = int(obj1[1])
        secondary_index_dict[obj[0]] = (start_pos, end_pos)

    return secondary_index_dict


def preprocess_raw_term(raw_term):
    '''
    1) Remove the punctutations
    2) Tokenize
    3) Case Folding
    4) Stop Words removal
    5) Stemming
    '''

    # Replace punctuation with space
    translator = string.maketrans(string.punctuation, ' ' * len(string.punctuation))
    raw_term = raw_term.translate(translator)
    # Doing Case folding
    raw_term = raw_term.lower()
    # Doing Tokenization
    tokens = raw_term.split()
    # Removing stop words
    stop_words = get_stop_words()
    tokens = [w for w in tokens if not w in stop_words]
    # Doing stemming
    stemmer = Stemmer.Stemmer('english')
    stemmed_tokens = stemmer.stemWords(tokens)

    return stemmed_tokens


def get_page_title_from_id(doc_id, page_title_id_filename):
    '''
    Get the page title from the page id using binary search
    '''
    doc_id = int(doc_id)
    fp = open(page_title_id_filename, 'r')

    l = 0
    r = os.path.getsize(page_title_id_filename)
    while (l < r):
        m = (l + r)/2
        fp.seek(m)
        # Read the partial string from (m to EOL)
        partial_string = fp.readline()
        # Now file pointer is in a new line
        next_line = fp.readline()
        # Get the id corresponding to next line
        obj = next_line.split(':', 1)
        this_id = int(obj[0])

        if this_id == doc_id:
            # Because the initial part of line is the <id>:
            return next_line.split(':', 1)[1].strip()
        elif this_id < doc_id:
            # The second half has to be traversed now
            l = m + 1
        else:
            # The left half has to be traversed now
            r = m - 1

    # Now l=r
    fp.seek(l)
    line = fp.readline()
    obj = line.split(':', 1)
    this_id = int(obj[0])
    if this_id == doc_id:
        # Because the initial part of line is the <id>:
        return line.split(':', 1)[1].strip()
    else:
        # Word not found
        return "Page ID Not Found"
