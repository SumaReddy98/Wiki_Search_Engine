import re
import sys
import os
import string
from lxml import etree as ET
import Stemmer
from collections import Counter

from merge import merge_indexes

stop_words = set(['all', 'pointing', 'four', 'go', 'oldest', 'seemed', 'whose', 'certainly', 'young', 'presents', 'to', 'asking', 'those', 'under', 'far', 'every', 'presented', 'did', 'turns', 'large', 'p', 'small', 'parted', 'smaller', 'says', 'second', 'further', 'even', 'what', 'anywhere', 'above', 'new', 'ever', 'full', 'men', 'here', 'youngest', 'let', 'groups', 'others', 'alone', 'along', 'great', 'k', 'put', 'everybody', 'use', 'from', 'working', 'two', 'next', 'almost', 'therefore', 'taken', 'until', 'today', 'more', 'knows', 'clearly', 'becomes', 'it', 'downing', 'everywhere', 'known', 'cases', 'must', 'me', 'states', 'room', 'f', 'this', 'work', 'itself', 'can', 'mr', 'making', 'my', 'numbers', 'give', 'high', 'something', 'want', 'needs', 'end', 'turn', 'rather', 'how', 'y', 'may', 'after', 'such', 'man', 'a', 'q', 'so', 'keeps', 'order', 'furthering', 'over', 'years', 'ended', 'through', 'still', 'its', 'before', 'group', 'somewhere', 'interesting', 'better', 'differently', 'might', 'then', 'non', 'good', 'somebody', 'greater', 'downs', 'they', 'not', 'now', 'gets', 'always', 'l', 'each', 'went', 'side', 'everyone', 'year', 'our', 'out', 'opened', 'since', 'got', 'shows', 'turning', 'differ', 'quite', 'members', 'ask', 'wanted', 'g', 'could', 'needing', 'keep', 'thing', 'place', 'w', 'think', 'first', 'already', 'seeming', 'number', 'one', 'done', 'another', 'open', 'given', 'needed', 'ordering', 'least', 'anyone', 'their', 'too', 'gives', 'interests', 'mostly', 'behind', 'nobody', 'took', 'part', 'herself', 'than', 'kind', 'b', 'showed', 'older', 'likely', 'r', 'were', 'toward', 'and', 'sees', 'turned', 'few', 'say', 'have', 'need', 'seem', 'saw', 'orders', 'that', 'also', 'take', 'which', 'wanting', 'sure', 'shall', 'knew', 'wells', 'most', 'nothing', 'why', 'parting', 'noone', 'later', 'm', 'mrs', 'points', 'fact', 'show', 'ending', 'find', 'state', 'should', 'only', 'going', 'pointed', 'do', 'his', 'get', 'cannot', 'longest', 'during', 'him', 'areas', 'h', 'she', 'x', 'where', 'we', 'see', 'are', 'best', 'said', 'ways', 'away', 'enough', 'smallest', 'between', 'across', 'ends', 'never', 'opening', 'however', 'come', 'both', 'c', 'last', 'many', 'against', 's', 'became', 'faces', 'whole', 'asked', 'among', 'point', 'seems', 'furthered', 'furthers', 'puts', 'three', 'been', 'much', 'interest', 'wants', 'worked', 'an', 'present', 'case', 'myself', 'these', 'n', 'will', 'while', 'would', 'backing', 'is', 'thus', 'them', 'someone', 'in', 'if', 'different', 'perhaps', 'things', 'make', 'same', 'any', 'member', 'parts', 'several', 'higher', 'used', 'upon', 'uses', 'thoughts', 'off', 'largely', 'i', 'well', 'anybody', 'finds', 'thought', 'without', 'greatest', 'very', 'the', 'yours', 'latest', 'newest', 'just', 'less', 'being', 'when', 'rooms', 'facts', 'yet', 'had', 'lets', 'interested', 'has', 'gave', 'around', 'big', 'showing', 'possible', 'early', 'know', 'like', 'necessary', 'd', 't', 'fully', 'become', 'works', 'grouping', 'because', 'old', 'often', 'some', 'back', 'thinks', 'for', 'though', 'per', 'everything', 'does', 'either', 'be', 'who', 'seconds', 'nowhere', 'although', 'by', 'on', 'about', 'goods', 'asks', 'anything', 'of', 'o', 'or', 'into', 'within', 'down', 'beings', 'right', 'your', 'her', 'area', 'downed', 'there', 'long', 'way', 'was', 'opens', 'himself', 'but', 'newer', 'highest', 'with', 'he', 'made', 'places', 'whether', 'j', 'up', 'us', 'problem', 'z', 'clear', 'v', 'ordered', 'certain', 'general', 'as', 'at', 'face', 'again', 'no', 'generally', 'backs', 'grouped', 'other', 'you', 'really', 'felt', 'problems', 'important', 'sides', 'began', 'younger', 'e', 'longer', 'came', 'backed', 'together', 'u', 'presenting', 'evenly', 'having', 'once'])

stop_words.add('page')
stop_words.add('nowiki')
stop_words.add('defaultsort')

# Adding file extensions to stopwords
stop_words.add('png')
stop_words.add('jpg')
stop_words.add('jpeg')
stop_words.add('txt')
stop_words.add('pdf')
stop_words.add('mp3')

# Combined Inverted Index for common queries
inverted_index = {}
# Inverted Index for Title queries
title_index = {}
# Inverted Index for Body
body_index = {}
# Inverted Index for Infobox queries
infobox_index = {}
# Inverted Index for Category queries
category_index = {}
# Inverted Index for References queries
references_index = {}
# Inverted Index for External Links
external_links_index = {}

# The file which contains the page_id to page_title mapping
page_id_title_fp = open("page_id_title.txt", "w")


# Maximum files that can be handled by MM
# max_files_session = 100000
max_files_session = 5000


def get_child(parent_element, child_element_name):
    for child in parent_element:
        if child.tag == child_element_name:
            return child

    return "Not Found"


def tokenize(info):
    '''
    This function removes punctuatuion in text and makes the tokens
    It also does the stop word removal
    '''

    # Removing Punctuation
    # Replace punctuation with space
    translator = string.maketrans(string.punctuation, ' ' * len(string.punctuation))
    info = info.translate(translator)
    # Doing Case folding
    info = info.lower()
    # Doing Tokenization
    tokens = info.split()
    # Removing stop words
    tokens = [w for w in tokens if not w in stop_words]

    return tokens


def stemming(tokens):
    '''
    Using Pystem to tokenize a list of words
    '''
    stemmer = Stemmer.Stemmer('english')
    stemmed_tokens = stemmer.stemWords(tokens)

    return stemmed_tokens


def cleanup(info):

    # Remove the hexadecimal color codes like '\x7f'
    info = re.sub('(\x7f|\x7F)', '', info)

    # Remove the https links
    url_links_regex = 'https?:\/\/.*?(\s|\|)'
    url_links_pattern = re.compile(url_links_regex)
    info = url_links_pattern.sub('\\1', info)

    # Remove the {{Link ...}} pattern
    info = re.sub('{{Link.*?}}', '', info)

    # Remove the {{fail ..}} pattern
    info = re.sub('{{[fF]ail.*?}}', '', info)

    # Remove {{citation needed}}
    info = re.sub('{{citation needed.*?}}', '', info)

    # Remove {{inconsistent citations}}
    info = re.sub('{{inconsistent citations.*?}}', '', info)

    # Remove {{reflist ... }} and {{Reflist ... }}
    info = re.sub('{{[rR]eflist.*?}}', '', info)

    # Remove {{refbegin ... }}
    info = re.sub('{{[rR]efbegin.*?}}', '', info)

    # Remove {{refend ... }}
    info = re.sub('{{[rR]efend.*?}}', '', info)

    # Remove {{R from CamelCase}} , {{R unprintworthy}} , {{R from misspelling}}
    info = re.sub('{{R\s.*?}}', '', info)

    # Remove the {{dead .. }}
    info = re.sub('{{[dD]ead.*?}}', '', info)

    # Remove the {{legend ... }}
    info = re.sub('{{[lL]egend.*?}}', '', info)

    # Remove the {{unreferenced ... }}
    info = re.sub('{{[uU]nreferenced.*?}}', '', info)

    # Remove the {{page needed ... }}
    info = re.sub('{{[pP]age.*?}}', '', info)

    # Remove the {{Authority control .... }}
    info = re.sub('{{[aA]uthority.*?}}', '', info)

    # Remove the {{#REDIRECT or #Redirect or #redirect}}
    info = re.sub('#[rR][eE][dD][iI][rR][eE][cC][tT]', '', info)

    # Remove the <math>...</math> tags
    info = re.sub('<math>(.|\\n)*?</math>', '', info)

    # Remove the <code> ... </code> tags
    info = re.sub('<code>(.|\\n)*?</code>', '', info)

    # Remove the <sup> ... </sup> tags
    info = re.sub('<sup>(.|\\n)*?</sup>', '', info)

    # Remove the <div ... > ... </div> tags
    info = re.sub('<div[^>]*?>', '', info)
    info = re.sub('<\/div>', '', info)

    # Remove the <syntaxhighlight ... > ... </syntaxhighlight>
    info = re.sub('<syntaxhighlight[^>]*?>((.|\\n)*?)<\/syntaxhighlight>', ' ', info)

    # Remove the {{zh icon}} part
    info = re.sub('{{zh.*?}}', ' ', info)

    # Remove the <br> or <br/> or <br />
    info = re.sub('<br(\s*\/)?>', ' ', info)

    # Remove the nbsp
    info = re.sub('&nbsp', ' ', info)

    # Remove the {{Use dmy dates|date=June 2013}}
    info = re.sub('{{[uU][sS][eE].*?}}', '', info)

    # Replace the {{Main|..}} pattern with {{..}}
    info = re.sub('{{Main(.*?)}}', '{{\\1}}', info)

    # Remove the Comments
    comments_regex = '<!--(.|\\n)*?-->'
    comments_pattern = re.compile(comments_regex)
    info = comments_pattern.sub('', info)

    return info


def mine(info, page_title, page_id):

    title_tokens_freq = {}
    body_tokens_freq = {}
    categories_tokens_freq = {}
    external_links_tokens_freq = {}
    infobox_tokens_freq = {}
    citations_tokens_freq = {}
    reftags_tokens_freq = {}
    further_readings_tokens_freq = {}
    see_also_tokens_freq = {}
    ref_headings_tokens_freq = {}

    if not info:
	   return [{}, {}, {}, {}, {}, {}, {}]

    page_title = page_title.encode('ascii', 'replace')
    title_tokens_freq = process_title(page_title)

    # First convert the info from utf-8 to ascii
    info = info.encode('ascii', 'replace')

    # Necessary wikipedia specific cleanup
    info = cleanup(info)

    # Get the categories_data
    categories_data = []
    # Regex of categories
    categories_regex = '\[\[Category:(.*)\]\]\\n'
    categories_pattern = re.compile(categories_regex)
    # Finding all such occurrences
    m = categories_pattern.findall(info)
    for match in m:
        match = match.strip()
        categories_data.append(match)
    categories_tokens_freq = process_categories(categories_data)
    # Removing the categories content from the Main text
    info = categories_pattern.sub('', info)


    # Get the external_links data
    external_links = ""
    # Regex of External Links
    external_links_regex = '==\s*External links\s*==((.|\\n)*?)\\n\\n'
    external_links_pattern = re.compile(external_links_regex)
    match = external_links_pattern.search(info)
    if match:
        external_links = match.group(1)
        external_links_tokens_freq = process_external_links(external_links)
        # Removing the External Links content from the Main text
        info = external_links_pattern.sub('', info)


    # Get the References
    # Part1 -> Get the citations ({{cite ...}})
    citations = []
    # Regex of citations
    citations_regex = '({{[cC]ite(.|\\n)*?}})'
    citations_pattern = re.compile(citations_regex)
    m = citations_pattern.findall(info)
    for match in m:
        citations.append(match[0])
    citations_tokens_freq = process_cites(citations)
    # Removing the citations
    info = citations_pattern.sub('', info)

    # Part2 -> Remove the <ref name='rertg' /> tags
    reftags = []
    # Regex of reftags for <ref name ... />
    reftag_regex1 = '(<ref name([^>])*?\/>)'
    reftag_pattern1 = re.compile(reftag_regex1)
    # Removing the ref tags content from the main text
    info = reftag_pattern1.sub('', info)

    # Part3 -> Get the <ref></ref> tags
    # Regex of reftags for <ref></ref>
    reftag_regex2 = '<ref[^>]*?>((.|\\n)*?)<\/ref>'
    reftag_pattern2 = re.compile(reftag_regex2)
    m = reftag_pattern2.findall(info)
    for match in m:
        reftags.append(match[0])
    reftags_tokens_freq = process_ref_tags(reftags)
    # Removing the ref tags content from the Main text
    info = reftag_pattern2.sub('', info)


    # Get the Infobox data
    infobox_data = []
    infobox_regex = '{{Infobox'
    patt = re.compile(infobox_regex)
    for match in re.finditer(patt, info):
        infobox_string = ""
        start_pos = match.span()[0]
        stack = ['{', '{']
        i = start_pos + 2
        while (i < len(info)) and (len(stack) > 0):
            infobox_string += info[i]
            if info[i] == '}':
                stack.pop()
            elif info[i] == '{':
                stack.append(info[i])
            i += 1
        infobox_string = infobox_string[:-2]
        infobox_data.append(infobox_string)
    infobox_tokens_freq = process_infobox(infobox_data)
    # Removing the infobox data
    for infobox_string in infobox_data:
        info = info.replace(infobox_string, '')


    # Get the ref_further_readings data
    ref_further_readings_data = ""
    # Regex of ref_further_readings data
    ref_further_readings_regex = '==\s*.*?further reading.*?\s*==((.|\\n)*?)\\n\\n'
    ref_further_readings_pattern = re.compile(ref_further_readings_regex)
    match = ref_further_readings_pattern.search(info)
    if match:
        ref_further_readings_data = match.group(1)
        further_readings_tokens_freq = process_further_readings(ref_further_readings_data)
        # Removing the See Also content from the Main text
        info = ref_further_readings_pattern.sub('', info)


    # Get the see_also data
    see_also_data = ""
    # Regex of see_also data
    see_also_regex = '==\s*See Also\s*==((.|\\n)*?)\\n\\n'
    see_also_pattern = re.compile(see_also_regex)
    match = see_also_pattern.search(info)
    if match:
        see_also_data = match.group(1)
        see_also_tokens_freq = process_see_also(see_also_data)
        # Removing the See Also content from the Main text
        info = see_also_pattern.sub('', info)


    # Processing the ==References== part
    ref_heading_data = ""
    # Regex of ==References== part
    ref_heading_regex = '==\s*References\s*==((.|\\n)*?)\\n\\n'
    ref_heading_pattern = re.compile(ref_heading_regex)
    match = ref_heading_pattern.search(info)
    if match:
        ref_heading_data = match.group(1)
        ref_headings_tokens_freq = process_ref_heading(ref_heading_data)
        # Removing the Ref Heading Content from Main text
        info = ref_heading_pattern.sub('', info)

    # Considering the leftover as the body and processing it
    body_tokens_freq = process_body(info)

    # Merge all the reference types into a single reference dict
    ref_tokens_freq = Counter(citations_tokens_freq) + Counter(reftags_tokens_freq) + Counter(further_readings_tokens_freq) + Counter(see_also_tokens_freq) + Counter(ref_headings_tokens_freq)
    ref_tokens_freq = dict(ref_tokens_freq)
    for word in ref_tokens_freq:
        ref_tokens_freq[word] = 'r' + str(ref_tokens_freq[word])

    # Indexing this doc by merging all the fields
    this_doc_index = {}
    this_doc_title_index = {}
    this_doc_body_index = {}
    this_doc_infobox_index = {}
    this_doc_category_index = {}
    this_doc_references_index = {}
    this_doc_external_links_index = {}

    vocab = list(set(title_tokens_freq.keys() + body_tokens_freq.keys() + categories_tokens_freq.keys() + external_links_tokens_freq.keys() + infobox_tokens_freq.keys() + ref_tokens_freq.keys()))
    for word in vocab:
		temp_str = page_id
		try:
			temp_str += str(title_tokens_freq[word])
                        title_string = page_id + str(title_tokens_freq[word])
                        try:
                            this_doc_title_index[word] += title_string + "|"
                        except:
                            this_doc_title_index[word] = title_string + "|"
		except:
			pass

		try:
			temp_str += str(body_tokens_freq[word])
                        body_string = page_id + str(body_tokens_freq[word])
                        try:
                            this_doc_body_index[word] += body_string + "|"
                        except:
                            this_doc_body_index[word] = body_string + "|"
		except:
			pass

		try:
			temp_str += str(infobox_tokens_freq[word])
                        infobox_string = page_id + str(infobox_tokens_freq[word])
                        try:
                            this_doc_infobox_index[word] += infobox_string + "|"
                        except:
                            this_doc_infobox_index[word] = infobox_string + "|"
		except:
			pass

		try:
			temp_str += str(categories_tokens_freq[word])
                        categories_string = page_id + str(categories_tokens_freq[word])
                        try:
                            this_doc_category_index[word] += categories_string + "|"
                        except:
                            this_doc_category_index[word] = categories_string + "|"
		except:
			pass

		try:
			temp_str += str(external_links_tokens_freq[word])
                        external_links_string = page_id + str(external_links_tokens_freq[word])
                        try:
                            this_doc_external_links_index[word] += external_links_string + "|"
                        except:
                            this_doc_external_links_index[word] = external_links_string + "|"
		except:
			pass

		try:
			temp_str += str(ref_tokens_freq[word])
                        references_string = page_id + str(ref_tokens_freq[word])
                        try:
                            this_doc_references_index[word] += references_string + "|"
                        except:
                            this_doc_references_index[word] = references_string + "|"
		except:
			pass

        # Adding postings to posting list
		try:
			this_doc_index[word] += temp_str+"|"
		except:
			this_doc_index[word] = temp_str+"|"

    return this_doc_index, this_doc_title_index, this_doc_body_index, this_doc_infobox_index, this_doc_category_index, this_doc_references_index, this_doc_external_links_index


def process_title(title):
    tokens = tokenize(title)
    stemmed_tokens = stemming(tokens)
    title_word_frequency = Counter(stemmed_tokens)
    title_word_frequency = dict(title_word_frequency)
    for word in title_word_frequency:
        title_word_frequency[word] = 't' + str(title_word_frequency[word])

    return title_word_frequency


def process_body(body):
    tokens = tokenize(body)
    stemmed_tokens = stemming(tokens)
    body_word_frequency = Counter(stemmed_tokens)
    body_word_frequency = dict(body_word_frequency)
    for word in body_word_frequency:
        body_word_frequency[word] = 'b' + str(body_word_frequency[word])

    return body_word_frequency


def process_infobox(infobox_list):
    # Stores all the words that needs to be indexed in a single string
    compressed_infobox_info = ''
    for infobox_info in infobox_list:
        items = infobox_info.split('|')
        # The first part is "Infobox disease" type stuff which is not needed
        items.pop(0)
        for item in items:
            # The content after = is to be indexed
            temp = item.split('=')
            # (Senators = Richard Shelby)
            if len(temp) != 2:
                continue
            val = temp[1].strip()
            if val != '':
                compressed_infobox_info += (val + " ")
    compressed_infobox_info = compressed_infobox_info.strip()

    tokens = tokenize(compressed_infobox_info)
    stemmed_tokens = stemming(tokens)
    infobox_word_frequency = Counter(stemmed_tokens)
    infobox_word_frequency = dict(infobox_word_frequency)
    for word in infobox_word_frequency:
        infobox_word_frequency[word] = 'i' + str(infobox_word_frequency[word])

    return infobox_word_frequency


def process_categories(categories_list):
    compressed_category_info = ""
    for category in categories_list:
        compressed_category_info += (category + " ")
    compressed_category_info = compressed_category_info.strip()

    tokens = tokenize(compressed_category_info)
    stemmed_tokens = stemming(tokens)
    category_word_frequency = Counter(stemmed_tokens)
    category_word_frequency = dict(category_word_frequency)
    for word in category_word_frequency:
        category_word_frequency[word] = 'c' + str(category_word_frequency[word])

    return category_word_frequency


def process_external_links(external_links):
    compressed_link_info = ""
    external_links = external_links.strip()
    links_list = external_links.split("\n")
    for link in links_list:
        if not link.startswith('*'):
            continue
        link_data = re.search('\*+([^\*]*)' , link).group(1)
        compressed_link_info += (link_data + " ")
    compressed_link_info = compressed_link_info.strip()

    tokens = tokenize(compressed_link_info)
    stemmed_tokens = stemming(tokens)
    external_links_word_frequency = Counter(stemmed_tokens)
    external_links_word_frequency = dict(external_links_word_frequency)
    for word in external_links_word_frequency:
        external_links_word_frequency[word] = 'e' + str(external_links_word_frequency[word])

    return external_links_word_frequency


def process_cites(citations_list):
    compressed_cite_info = ""
    for cite in citations_list:
        # Removing {{}}
        cite = cite[2:-2]
        items = cite.split('|')
        # The first item is cite web (or) cite book (or) cite journal
        items.pop(0)
        for item in items:
            # The content after = is to be indexed
            temp = item.split('=')
            if len(temp) != 2:
                continue
            val = temp[1].strip()
            if val != '':
                compressed_cite_info += (val + " ")
    compressed_cite_info = compressed_cite_info.strip()

    tokens = tokenize(compressed_cite_info)
    stemmed_tokens = stemming(tokens)
    cites_word_frequency = Counter(stemmed_tokens)

    return cites_word_frequency


def process_ref_tags(reftags_list):
    compressed_reftag_info = ' '
    for reftag_data in reftags_list:
        reftag_data = reftag_data.strip()
        compressed_reftag_info += (reftag_data + " ")
    compressed_reftag_info = compressed_reftag_info.strip()

    tokens = tokenize(compressed_reftag_info)
    stemmed_tokens = stemming(tokens)
    reftags_word_frequency = Counter(stemmed_tokens)

    return reftags_word_frequency


def process_further_readings(further_readings_data):
    compressed_further_readings_info = ""
    further_readings_data = further_readings_data.strip()
    further_readings_list = further_readings_data.split("\n")
    for reading in further_readings_list:
        if not reading.startswith('*'):
            continue
        reading_data = re.search('\*+([^\*]*)' , reading).group(1)
        compressed_further_readings_info += (reading_data + " ")
    compressed_further_readings_info = compressed_further_readings_info.strip()

    tokens = tokenize(compressed_further_readings_info)
    stemmed_tokens = stemming(tokens)
    further_readings_word_frequency = Counter(stemmed_tokens)

    return further_readings_word_frequency


def process_see_also(see_also_data):
    compressed_see_also_info = ""
    see_also_data = see_also_data.strip()
    see_also_list = see_also_data.split("\n")
    for item in see_also_list:
        if not item.startswith('*'):
            continue
        item_data = re.search('\*+([^\*]*)' , item).group(1)
        compressed_see_also_info += (item_data + " ")
    compressed_see_also_info = compressed_see_also_info.strip()

    tokens = tokenize(compressed_see_also_info)
    stemmed_tokens = stemming(tokens)
    see_also_word_frequency = Counter(stemmed_tokens)

    return see_also_word_frequency


def process_ref_heading(ref_heading_data):
    compressed_ref_heading_info = ""
    ref_heading_data = ref_heading_data.strip()
    ref_heading_list = ref_heading_data.split("\n")
    for item in ref_heading_list:
        if not item.startswith('*'):
            continue
        item_data = re.search('\*+([^\*]*)' , item).group(1)
        compressed_ref_heading_info += (item_data + " ")
    compressed_ref_heading_info = compressed_ref_heading_info.strip()

    tokens = tokenize(compressed_ref_heading_info)
    stemmed_tokens = stemming(tokens)
    refheading_word_frequency = Counter(stemmed_tokens)

    return refheading_word_frequency


def process_page(page_element):
    '''
    We get a lxml element object, which contains info about a wiki page
    We need to extract the different fields from this
    The fields are
        1) Title
        2) Body Content
        3) Infobox Content
        4) Categories
        5) External Links
        6) References
    This function returns these fields
    '''
    global inverted_index

    page_title = ""
    page_id = ""
    for child in page_element:
        if child.tag == "title":
            page_title = child.text
        elif child.tag == "id":
            page_id = child.text
        elif child.tag == "revision":
            # confirmed that the whole text info is inside the revision tag
            text_element = get_child(child, "text")
            info = text_element.text
            break

    # if str(page_id) == "620":
    #     this_doc_word_frequency = mine(info, page_title, page_id)
    #     for word in this_doc_word_frequency:
    #         if word in inverted_index:
    #             inverted_index[word] += this_doc_word_frequency[word]
    #         else:
    #             inverted_index[word] = this_doc_word_frequency[word]

    # Write to the map of page id to page title
    page_id_title_fp.write(str(page_id) + ":" + str(page_title.encode('ascii', 'ignore')) + "\n")

    indexes = mine(info, page_title, page_id)

    this_doc_index = indexes[0]
    this_doc_title_index = indexes[1]
    this_doc_body_index = indexes[2]
    this_doc_infobox_index = indexes[3]
    this_doc_category_index = indexes[4]
    this_doc_references_index = indexes[5]
    this_doc_external_links_index = indexes[6]

    # Merging the doc index with global index
    for word in this_doc_index:
        if word in inverted_index:
            inverted_index[word] += this_doc_index[word]
        else:
            inverted_index[word] = this_doc_index[word]

    # Merging the doc title index with global title index
    for word in this_doc_title_index:
        if word in title_index:
            title_index[word] += this_doc_title_index[word]
        else:
            title_index[word] = this_doc_title_index[word]

    # Merging the doc body index with global body index
    for word in this_doc_body_index:
        if word in body_index:
            body_index[word] += this_doc_body_index[word]
        else:
            body_index[word] = this_doc_body_index[word]

    # Merging the doc infobox index with global infobox index
    for word in this_doc_infobox_index:
        if word in infobox_index:
            infobox_index[word] += this_doc_infobox_index[word]
        else:
            infobox_index[word] = this_doc_infobox_index[word]

    # Merging the doc category index with global category index
    for word in this_doc_category_index:
        if word in category_index:
            category_index[word] += this_doc_category_index[word]
        else:
            category_index[word] = this_doc_category_index[word]

    # Merging the doc references index with global references index
    for word in this_doc_references_index:
        if word in references_index:
            references_index[word] += this_doc_references_index[word]
        else:
            references_index[word] = this_doc_references_index[word]

    # Merging the doc external links index with global external links index
    for word in this_doc_external_links_index:
        if word in external_links_index:
            external_links_index[word] += this_doc_external_links_index[word]
        else:
            external_links_index[word] = this_doc_external_links_index[word]


def write_index_file(file_name, index):
    '''
    This function writes the content of index into the file_name
    '''

    # Create the file if not present
    if not os.path.exists(os.path.dirname(file_name)):
            os.makedirs(os.path.dirname(file_name))

    index_fp = open(file_name, "w")
    for word in sorted(index):
        # Remove the last '|' in the index
        entry = index[word][:-1]
        index_fp.write(word + ":" + entry + "\n")
    index_fp.close()



def main():
    global inverted_index
    global title_index
    global body_index
    global infobox_index
    global category_index
    global references_index
    global external_links_index

    xml_file_path = sys.argv[1]

    files_processed = 0
    # Segments of sorted indexes for different docs
    num_temp_index_files = 0

    for event, element in ET.iterparse(xml_file_path):
        # The below cmnd removes the namespace of the xml tags
        element.tag = ET.QName(element.tag).localname
        if not element.tag.startswith("page"):
            continue

        # Process the page to extract the fields
        process_page(element)
        element.clear()

        files_processed += 1
        print files_processed

        # Write the index dump for every max_files_session files processed
        if (files_processed % max_files_session) == 0:
                num_temp_index_files += 1
                write_index_file("./index_files/temp_index_" + "global" + str(num_temp_index_files) + ".txt" , inverted_index)
                write_index_file("./index_files/temp_index_" + "title" + str(num_temp_index_files) + ".txt" , title_index)
                write_index_file("./index_files/temp_index_" + "body" + str(num_temp_index_files) + ".txt" , body_index)
                write_index_file("./index_files/temp_index_" + "infobox" + str(num_temp_index_files) + ".txt" , infobox_index)
                write_index_file("./index_files/temp_index_" + "category" + str(num_temp_index_files) + ".txt" , category_index)
                write_index_file("./index_files/temp_index_" + "references" + str(num_temp_index_files) + ".txt" , references_index)
                write_index_file("./index_files/temp_index_" + "external_links" + str(num_temp_index_files) + ".txt" , external_links_index)

                inverted_index = {}
                title_index = {}
                body_index = {}
                infobox_index = {}
                category_index = {}
                references_index = {}
                external_links_index = {}

    # Dump the leftover files index
    if len(inverted_index) > 0:
        num_temp_index_files += 1
        write_index_file("./index_files/temp_index_" + "global" + str(num_temp_index_files) + ".txt" , inverted_index)
        write_index_file("./index_files/temp_index_" + "title" + str(num_temp_index_files) + ".txt" , title_index)
        write_index_file("./index_files/temp_index_" + "body" + str(num_temp_index_files) + ".txt" , body_index)
        write_index_file("./index_files/temp_index_" + "infobox" + str(num_temp_index_files) + ".txt" , infobox_index)
        write_index_file("./index_files/temp_index_" + "category" + str(num_temp_index_files) + ".txt" , category_index)
        write_index_file("./index_files/temp_index_" + "references" + str(num_temp_index_files) + ".txt" , references_index)
        write_index_file("./index_files/temp_index_" + "external_links" + str(num_temp_index_files) + ".txt" , external_links_index)

        inverted_index = {}
        title_index = {}
        body_index = {}
        infobox_index = {}
        category_index = {}
        references_index = {}
        external_links_index = {}


    # Merge all the index files and name the whole huge index as index_file_path
    merge_indexes("global", num_temp_index_files, files_processed)
    merge_indexes("title", num_temp_index_files, files_processed)
    merge_indexes("body", num_temp_index_files, files_processed)
    merge_indexes("category", num_temp_index_files, files_processed)
    merge_indexes("infobox", num_temp_index_files, files_processed)
    merge_indexes("references", num_temp_index_files, files_processed)
    merge_indexes("external_links", num_temp_index_files, files_processed)


if __name__ == "__main__":
    main()
