## Download Coursera materials.

### Dependencies:
* Python 2.7 - for argparse
* Mechanize
* BeautifulSoup

### Format:
python coursera.py &lt;course&gt; [-p part1 part2 ...] [-r row1 row2 ...] [-t {pdf ppt txt srt movie} {pdf ppt txt srt movie} ...] [-v] [-l {debug info warning error critical}] [-f] [-e]

* course - the course name, just look for the according name in the url of the course
* -p or --parts - numbers starting from 1 of nessesary chapters (optional)
* -r or --rows - numbers starting from 1 of nessesary lectures (optional)
* -t or --types - types of resources to download (optional)
* -v or --verbose - be verbose (the same as -l info) (optional)
* -l or --logging - use specified logging level (optional)
* -f or --force - override existing files (optional)
* -e or --escape - escape file and directory names (important for Windows) (optional)

### Examples:
* python coursera.py nlp -v -e - download the whole NLP course in verbose mode and escape file names (skip already downloaded files)
* python coursera.py saas -v -f - download the whole SAAS course in verbose mode (override existing files)
* python coursera.py saas -l debug -f - download the whole SAAS course with debug logging level (override existing files)
* python coursera.py nlp -p 1 2 -v - download the 1st and the 2nd chapters of NLP course
* python coursera.py nlp -p 3  -r 2 3 - download the 2nd and the 3rd lectures of the 3rd chapter of NLP course
* python coursera.py nlp -p 3  -r 2 3 -t movie pdf - download the 2nd and the 3rd lectures of the 3rd chapter of NLP course (only video and PDF files)
