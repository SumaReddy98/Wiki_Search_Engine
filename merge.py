import heapq
import os
from util import get_champions_list
from util import get_tfidf_added_list

def merge_indexes(index_type, num_temp_index_files, total_number_documents):
    '''
    Merge the indexes which belong to a certain field and get the primary and secondary indexes
    Primary indexes are placed inside the directory "Primary_Indexes" as <index_type>.txt
    Secondary indexes are placed inside the directory "Secondary_Indexes" as <index_type>.txt
    index_type can be only global, title, body, category, infobox, references, external_links
    '''

    # Create the directory "Primary_Indexes" if not present
    try:
        os.makedirs("Primary_Indexes")
    except:
        # Means that the directory already exists
        pass

    # Create the directory "Secondary_Indexes" if not present
    try:
        os.makedirs("Secondary_Indexes")
    except:
        # Means that the directory already exists
        pass

    # Primary index stores the merged words
    f_primary_index = open("Primary_Indexes/" + index_type + ".txt", "w")

    # Secondary index stores the starting line beginning offset and ending line beginning offset
    f_secondary_index = open("Secondary_Indexes/" + index_type + ".txt", "w")

    # Creating map from file numbers to their respective file pointers
    list_file_pointers = {}
    for i in range(1, num_temp_index_files + 1):
        f = open("./index_files/temp_index_" + index_type + str(i) + ".txt")
        list_file_pointers[i] = f

    # Storing the first lines of all files and the file number in which it occurred
    heap = []
    for i in range(1, num_temp_index_files + 1):
        first_line = str(list_file_pointers[i].readline().strip())
        obj = first_line.split(':')
        word = obj[0]
        posting_list = obj[1]

        # Get the starting doc id
        starting_doc_id = ""
        for ch in posting_list:
            if ch.isdigit():
                starting_doc_id += ch
            else:
                break

        heap.append((word, starting_doc_id, posting_list, i))

    # Converting the list to heap => O(n)
    heapq.heapify(heap)

    # stores the first character in the final index
    trend = None
    offset = 0
    previous_line_length = 0
    start = {}
    end = {}

    while (len(heap) > 0):
        # Getting the alphabetically least words
        least_word = heap[0][0]
        least_word_posting_list = ""
        file_consumed_num = []
        while (len(heap) > 0 and heap[0][0] == least_word):
                least_word_obj = heapq.heappop(heap)
                least_word_posting_list = least_word_posting_list + "|" + least_word_obj[2]
                file_consumed_num.append(least_word_obj[3])

        # Removing the first '|' in the merged posting list
        least_word_posting_list = least_word_posting_list[1:]

        # Making the champion list. This also adds the tfidf value in each posting
        # least_word_champion_list = get_champions_list(least_word_posting_list, total_number_documents, 1000)
        # Adding the tfidf values to the posting list, without champions
        least_word_champion_list = get_tfidf_added_list(least_word_posting_list, total_number_documents)
        # Writing the result to the main index file
        line_to_write = least_word + ":" + least_word_champion_list + "\n"
        f_primary_index.write(line_to_write)

        # Secondary index logic
        this_word_trend = least_word[0]
        if this_word_trend != trend:
            if trend != None:
                # Because we want the line beginning of the last word belonging to the trend
                end[trend] = offset - previous_line_length
            trend = this_word_trend
            start[trend] = offset

        offset += len(line_to_write)
        previous_line_length = len(line_to_write)

        # Extract next line from the files whose first line has been consumed
        for file_num in file_consumed_num:
            next_line = list_file_pointers[file_num].readline().strip()
            if not next_line:
                continue
            obj = next_line.split(':')
            word = obj[0]
            posting_list = obj[1]

            # Get the starting doc id
            starting_doc_id = ""
            for ch in posting_list:
                if ch.isdigit():
                    starting_doc_id += ch
                else:
                    break

            heapq.heappush(heap, (word, starting_doc_id, posting_list, file_num))

    # Because the end term will not be decided for the last entries if not done below step
    end[trend] = offset - previous_line_length

    # Writing the secondary index
    for key in sorted(start):
        f_secondary_index.write( str(key) + " : " + str(start[key]) + "," + str(end[key]) + "\n" )

    f_primary_index.close()
    f_secondary_index.close()
    for key in list_file_pointers:
        list_file_pointers[key].close()


def main():
    num_temp_index_files = 177
    files_processed = 17640866
    merge_indexes("global", num_temp_index_files, files_processed)
    merge_indexes("title", num_temp_index_files, files_processed)
    merge_indexes("body", num_temp_index_files, files_processed)
    merge_indexes("category", num_temp_index_files, files_processed)
    merge_indexes("infobox", num_temp_index_files, files_processed)
    merge_indexes("references", num_temp_index_files, files_processed)
    merge_indexes("external_links", num_temp_index_files, files_processed)
