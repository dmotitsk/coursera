##Download Coursera materials.

###Dependencies:
* Python 2.7 - for argparse
* Mechanize
* BeautifulSoup

###Format:
python coursera.py &lt;course&gt; [-p part1 part2 ...] [-r row1 row2 ...] [-t {pdf ppt txt srt movie} {pdf ppt txt srt movie} ...] [-v] [-f]

* course - the course name, just look for the according name in the urls of the course
* -p or --parts - numbers starting from 1 of nessesary chapters (optional)
* -r or --rows - numbers starting from 1 of nessesary lectures (optional)
* -t or --types - types of resources to download (optional)
* -v or --verbose - be more verbose (optional)
* -f or --force - override existing files (optional)
