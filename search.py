import os
import sys
import heapq
import time
from util import get_word
from util import extract_data_posting
from util import parse_secondary_index
from util import preprocess_raw_term
from util import get_page_title_from_id

# The directory which contains the Index results
prefix_directory = None
page_id_title_filename = None

def get_posting_list(word, starting_pos, ending_pos, file_pointer):
    '''
        Get the posting list regarding the word using the secondary index
    which has the starting and ending positions(offsets of the file)
    of the starting alphabet of the word in the file indicated by the
    file_pointer
        We do Binary Search on the positions

    @word : C{String}
    @primary_index_file_name : C{String}
    @secondary_index_file_name : C{String}

    @return : Returns the posting list of the word as a string
    '''

    l = int(starting_pos)
    r = int(ending_pos)
    while (l<r):
        m = (l+r)/2
        file_pointer.seek(m)
        # Read the partial string from (m to EOL)
        partial_string = file_pointer.readline()
        # Now file pointer is in a new line
        next_line = file_pointer.readline()
        # Get the token corresponding to next line
        this_word = get_word(next_line)
        if this_word == word:
            # Because the initial part of line is the <word>:
            return next_line.split(':', 1)[1]
        elif this_word < word:
            # The second half has to be traversed now
            l = m + 1
        else:
            # The left half has to be traversed now
            r = m - 1

    # Now l=r
    file_pointer.seek(l)
    line = file_pointer.readline()
    this_word = get_word(line)
    if this_word == word:
        # Because the initial part of line is the <word>:
        return line.split(':', 1)[1]
    else:
        # Word not found
        return ""


def morph_posting_list(posting_list):
    '''
    Convert the posting list in string format
    to
    A list of ( tfifd_value, doc_id) tuples
    '''
    if not isinstance(posting_list, str):
        # It is a list of tuples and hence return it
        return posting_list

    pl = posting_list.split('|')
    for i in range(len(pl)):
        obj = extract_data_posting(pl[i])
        doc_id = obj[0]
        tfidf = obj[1]
        pl[i] = (tfidf, doc_id)

    return pl


def merge_posting_lists(pl1, pl2):
    '''
    Merges the 2 posting lists sorted by the doc id's
    If 2 elements have the same doc id, then the tf-idf values are added

    @param pl1 : C{Str} or C{list}
    @param pl2 : C{Str} or C{list}
    '''

    merged_pl = []

    list1 = morph_posting_list(pl1)
    list2 = morph_posting_list(pl2)

    if len(list1) == 0:
        return list2
    if len(list2) == 0:
        return list1

    i = 0
    j = 0
    while i < len(list1) and j < len(list2):
        tfidf1 = list1[i][0]
        doc_id1 = list1[i][1]

        tfidf2 = list2[j][0]
        doc_id2 = list2[j][1]

        if doc_id1 < doc_id2:
            i += 1

        elif doc_id1 > doc_id2:
            j += 1

        else:
            # doc_id1 = doc_id2
            merged_pl.append((round(tfidf1 + tfidf2, 3), doc_id1))
            i += 1
            j += 1

    return merged_pl


def show_results(query_terms, primary_indexes_fp_dicts, secondary_indexes_dicts):
    '''
    This function retrieves the top k results (doc_ids) from the query query_terms
    query_terms is a dict of terms(Strings) with values as fields

    The query terms would be either <word> or <field_symbol>:<word>
    <field_symbol> can be only t,b,c,i,r,e

    @param query_terms : C{Dict[Word:Field]}
    @param primary_index_fp_dict : list of file pointer for the primary index, one for each field
    @param secondary_index_dict : list of Dictionary storing a list of start and end offset positions for each character, each for one field
    '''

    k = 10

    combined_pl = []
    for term in query_terms:
        # Getting the field corresponding to the term
        field = query_terms[term]
        # Getting the starting and ending positions
        starting_pos = secondary_indexes_dicts[field][term[0]][0]
        ending_pos   = secondary_indexes_dicts[field][term[0]][1]
        # Get the posting list
        pl = get_posting_list(term, starting_pos, ending_pos, primary_indexes_fp_dicts[field])
        # Merge the posting list
        combined_pl = merge_posting_lists(combined_pl, pl)

    # heapq.heapify(combined_pl)
    combined_pl.sort(reverse = True)
    sorted_results = combined_pl
    # top_k_results = heapq.nlargest(k, combined_pl)

    if len(sorted_results) == 0:
        print "No Results Found"
        return

    files_showed = 0
    for result in sorted_results:
        if files_showed == k:
            break
        doc_id = result[1]
        page_title = get_page_title_from_id(doc_id, page_id_title_filename)
        if len(sorted_results) <= 10:
            # Don't delete the wikipedia pages if the number of results are below 10
            files_showed += 1
            print doc_id, result[0], page_title
        else:
            if not page_title.startswith('Wikipedia:'):
                files_showed += 1
                print doc_id, result[0], page_title
    print

    return


def get_query_from_user(primary_indexes_fp_dicts, secondary_indexes_dicts):
    while(1):
        raw_query = raw_input(">>> ")
        start_time = time.time()
        # The query_terms may have fields in them also in the format <field_char>:raw_term
        query_terms = raw_query.split()
        # Dict b/w raw_query_terms and their respective fields(g,t,b,c,i,e,r)
        raw_query_terms = {}
        for query_term in query_terms:
            obj = query_term.split(':', 1)
            field = 'g'
            raw_term = obj[0]
            if len(obj) == 2:
                if (obj[0] == 't') or (obj[0] == 'b') or (obj[0] == 'c') or (obj[0] == 'i') or (obj[0] == 'e') or (obj[0] == 'r'):
                    field = obj[0]
                    raw_term = obj[1]
                else:
                    field = 'g'
                    raw_term = query_term

            # b:title,banana
            list_terms = preprocess_raw_term(raw_term)
            for term in list_terms:
                raw_query_terms[term] = field

        print raw_query_terms
        # Getting the results based on all the query terms
        show_results(raw_query_terms, primary_indexes_fp_dicts, secondary_indexes_dicts)
        end_time = time.time()
        print "Time Taken : " + str(end_time - start_time) + " seconds"
        print



def main():
    global prefix_directory
    global page_id_title_filename

    prefix_directory = sys.argv[1] + "/"
    page_id_title_filename = prefix_directory + 'page_id_title.txt'

    # Open the primary indexes
    primary_indexes_fp_dicts = {}
    primary_indexes_fp_dicts['g'] = open(prefix_directory + 'Primary_Indexes/global.txt', 'r')
    primary_indexes_fp_dicts['t'] = open(prefix_directory + 'Primary_Indexes/title.txt', 'r')
    primary_indexes_fp_dicts['b'] = open(prefix_directory + 'Primary_Indexes/body.txt', 'r')
    primary_indexes_fp_dicts['c'] = open(prefix_directory + 'Primary_Indexes/category.txt', 'r')
    primary_indexes_fp_dicts['i'] = open(prefix_directory + 'Primary_Indexes/infobox.txt', 'r')
    primary_indexes_fp_dicts['r'] = open(prefix_directory + 'Primary_Indexes/references.txt', 'r')
    primary_indexes_fp_dicts['e'] = open(prefix_directory + 'Primary_Indexes/external_links.txt', 'r')

    # Open and parse the secondary indexes
    secondary_indexes_dicts = {}
    for filename in os.listdir(prefix_directory + 'Secondary_Indexes'):
        fp = open(prefix_directory + 'Secondary_Indexes/' + filename)
        parsed_secondary_index = parse_secondary_index(fp)
        if filename == 'global.txt':
            secondary_indexes_dicts['g'] = parsed_secondary_index
        elif filename == 'title.txt':
            secondary_indexes_dicts['t'] = parsed_secondary_index
        elif filename == 'body.txt':
            secondary_indexes_dicts['b'] = parsed_secondary_index
        elif filename == 'category.txt':
            secondary_indexes_dicts['c'] = parsed_secondary_index
        elif filename == 'infobox.txt':
            secondary_indexes_dicts['i'] = parsed_secondary_index
        elif filename == 'references.txt':
            secondary_indexes_dicts['r'] = parsed_secondary_index
        elif filename == 'external_links.txt':
            secondary_indexes_dicts['e'] = parsed_secondary_index

    get_query_from_user(primary_indexes_fp_dicts, secondary_indexes_dicts)

if __name__ == '__main__':
    main()
