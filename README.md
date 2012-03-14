##Download Coursera materials.

###Dependencies:
* Python 2.7 - for argparse
* Mechanize
* BeautifulSoup

###Format:
python coursera.py &lt;course&gt; [-p part1 part2 ...] [-r row1 row2 ...] [-t {pdf ppt txt movie} {pdf ppt txt movie} ...]

* course - currently 'saas' or 'nlp' (it should also work with other courses, just add a new class with URL's overriden)
* parts - numbers starting from 1 of nessesary chapters (optional)
* rows - numbers starting from 1 of nessesary lectures (optional)
* types - types of resources to download (optional)
