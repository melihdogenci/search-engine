import urllib.request
import ssl

def getPage(url):
    """
    Fetches the content of a webpage given its URL.

    Args:
        url (str): The URL of the webpage to fetch.

    Returns:
        str: The content of the webpage as a UTF-8 encoded string. If the request fails or an exception occurs, returns an empty string.
    """
    try:
        context = ssl._create_unverified_context()
        page = urllib.request.urlopen(url, context=context).read()
        page = page.decode("utf-8")
        return page
    except Exception as e:
        print(f"Error: {e}")
        return ""



def union(set1, set2):
    """
    Update set1 with elements from set2.

    Args:
    - set1 (set): The set to be updated.
    - set2 (set): The set with elements to add.

    Returns:
    - set: The updated set1.
    """
    set1.update(set2)
    return set1


def addToIndex(index, keyword, url):
    """
    Add a URL to the index under a specific keyword.

    Args:
    - index (dict): The index to be updated.
    - keyword (str): The keyword to index the URL under.
    - url (str): The URL to be added to the index.
    """
    if keyword in index:
        index[keyword].append(url)
    else:
        index[keyword] = [url]


def addPageToIndex(index, url, content):
    """
    Add all words from the page content to the index.

    Args:
    - index (dict): The index to be updated.
    - url (str): The URL of the page.
    - content (str): The content of the page.
    """
    words = content.split()
    for word in words:
        addToIndex(index, word, url)
    return index


def extractBaseLink(link):
    """
    Extract the base URL from an absolute URL.

    Args:
    - link (str): The absolute URL.

    Returns:
    - str: The base URL if the input link is absolute, otherwise None.
    """
    if link.startswith('http://') or link.startswith('https://'):
        parts = link.split('/')
        return parts[0] + '//' + parts[2]
    return None


def linkFinder(page, baseUrl=None):
    """
    Extract absolute URLs from the HTML content of a web page.

    Args:
    - page (str): The HTML content of the web page as a string.
    - baseUrl (str, optional): The base URL to resolve relative URLs against. If not provided, only absolute URLs are processed.

    Returns:
    - set: A set of absolute URLs found in the page. URLs are filtered to include only those starting with 'http://' or 'https://'.

    Notes:
    - Handles protocol-relative URLs (e.g., `//example.com`) by converting them to `http://`.
    - Resolves relative URLs using the provided `baseUrl`. If `baseUrl` is not provided, relative URLs are ignored.
    - Removes URL fragments (e.g., `#section`) as they are not necessary for link processing.
    - Filters out URLs with unsupported schemes (e.g., `mailto:`, `ftp:`).

    Example:
    >>> html_content = '<a href="/path/to/resource">Link</a><a href="https://example.com">Absolute Link</a>'
    >>> linkFinder(html_content, baseUrl='https://example.com')
    {'https://example.com/path/to/resource', 'https://example.com'}
    """
    urls = set()
    baseUrl = baseUrl or ''

    while True:
        startPoint = page.find("<a href=")
        if startPoint == -1:
            break

        startQuote = page.find('"', startPoint)
        endQuote = page.find('"', startQuote + 1)
        link = page[startQuote + 1:endQuote]
        page = page[endQuote + 1:]

        # Handle fragment
        if '#' in link:
            link = link.split('#')[0]  # Ignore fragment part

        # Handle protocol-relative URLs
        if link.startswith('//'):
            link = 'http:' + link

        # Handle relative URLs
        if not link.startswith('http://') and not link.startswith('https://'):
            if baseUrl:
                if link.startswith('/'):
                    link = baseUrl + link
                else:
                    link = baseUrl + '/' + link

        # Filter for HTTP/HTTPS URLs
        if link.startswith('http://') or link.startswith('https://'):
            urls.add(link)

    return urls


def crawlWeb(seed):
    """
    Crawl a web page and build an index and a graph of pages.

    Args:
    - seed (str): The seed URL to start crawling from.

    Returns:
    - tuple: A tuple containing the index (dict) and the graph (dict).
    """
    tocrawl = {seed}
    crawled = set()
    index = {}
    graph = {}

    while tocrawl:
        page = tocrawl.pop()
        if page not in crawled:
            content = getPage(page)
            addPageToIndex(index, page, content)
            outlinks = linkFinder(content)
            graph[page] = outlinks
            union(tocrawl, outlinks)
            crawled.add(page)
    return index, graph


def computeRanks(graph):
    """
    Compute PageRank for each page in the graph.

    Args:
    - graph (dict): The graph where keys are pages and values are sets of outgoing links.

    Returns:
    - dict: A dictionary with pages as keys and their PageRank as values.
    """
    damping = 0.8
    numloops = 10
    ranks = {}
    npages = len(graph)

    for page in graph:
        ranks[page] = 1 / npages

    for i in range(numloops):
        newrank = {}
        for page in graph:
            newrank[page] = (1 - damping) / npages
            for node in graph:
                if page in graph[node]:
                    newrank[page] += damping * (ranks[node] / len(graph[node]))
        ranks = newrank

    return ranks


def lookUpRanked(index, keyword, ranks):
    """
    Look up pages related to a keyword and sort them by their PageRank.

    Args:
    - index (dict): The index where keywords map to lists of URLs.
    - keyword (str): The keyword to search for.
    - ranks (dict): The PageRank values for each page.

    Returns:
    - list: A list of URLs sorted by PageRank in descending order.
    """
    readyToSort = {}
    keyword = keyword.lower()

    for word in index.keys():
        if keyword in word.lower():
            unsortedlist = index[word]
            for elements in unsortedlist:
                readyToSort[elements] = ranks.get(elements, 0)

    if readyToSort:
        return sorted(readyToSort, key=readyToSort.get, reverse=True)
    return None


# Main execution
index, graph = crawlWeb('https://searchengineplaces.com.tr/')
ranks = computeRanks(graph)
print(lookUpRanked(index, "oktay", ranks))