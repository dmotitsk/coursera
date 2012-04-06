import argparse
import os
import re
import sys

try:
    from BeautifulSoup import BeautifulSoup
    from mechanize import Browser
except ImportError:
    print ("Not all the nessesary libs are installed. " +
           "Please see requirements.txt.")
    sys.exit(1)

from soupselect import select
try:
    from config import EMAIL, PASSWORD
except ImportError:
    print "You should provide config.py file with EMAIL and PASSWORD."
    sys.exit(1)

try:
    from config import TARGETDIR
except ImportError:
    TARGETDIR = ''

try:
    from config import ESCAPE_FILE_NAME
except ImportError:
    ESCAPE_FILE_NAME = False


ILLEGAL_CHARS = ('<', '>', ':', '"', '|', '?', '*')
REG_URL_FILE = re.compile(r'.*/([^./]+)\.([\w\d]+)$', re.I)
REG_CONT_TYPE_EXT = re.compile(r'^.*/([\d\w]+)$', re.I)
REG_TXT_RES = re.compile(r'^(.*format)=txt$', re.I)
TYPES = ('pdf', 'ppt', 'txt', 'srt', 'movie')

# This dictionary is needed for not changing program interface
# every time Coursera changes type icon names.
TYPE_REPLACEMENT = {
    'txt': 'subtitles (text)', 'srt': 'subtitles (srt)',
    'movie': 'video (mp4)'
}
DEFAULT_EXT = {
    'pdf': 'pdf', 'ppt': 'ppt', 'subtitles (text)': 'txt',
    'subtitles (srt)': 'srt', 'video (mp4)': 'mp4'
}

verbose = 0


class CourseraDownloader(object):
    login_url = ''
    home_url = ''
    lectures_url = ''
    course_name = ''

    def __init__(self, config):
        self.parts_ids = config['parts']
        self.rows_ids = config['rows']
        self.types = config['types']
        self.force = config['force']
        self.br = Browser()
        self.br.set_handle_robots(False)

    def authenticate(self):
        self.br.open(self.login_url)
        self.br.form = self.br.forms().next()
        self.br['email'] = EMAIL
        self.br['password'] = PASSWORD
        self.br.submit()
        home_page = self.br.open(self.home_url)
        if not self.is_authenticated(home_page.read()):
            log("couldn't authenticate")
            sys.exit(1)
        log("successfully authenticated")

    def is_authenticated(self, test_page):
        m = re.search(
            'https://class.coursera.org/%s/auth/logout' % self.course_name,
            test_page)
        return m is not None

    def download(self):
        course_dir = os.path.join(TARGETDIR, self.course_name)
        if not os.path.exists(course_dir):
            os.mkdir(course_dir)
        page = self.br.open(self.lectures_url)
        doc = BeautifulSoup(page)
        parts, part_titles = self.get_parts(doc)
        for idx, part in enumerate(parts):
            if self.item_is_needed(self.parts_ids, idx):
                part_dir = os.path.join(
                    course_dir,
                    '%02d - %s' % ((idx + 1),
                    self.escape_name(part_titles[idx].text.strip())))
                self.download_part(part_dir, part)

    def download_part(self, dir_name, part):
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
        rows, row_names = self.get_rows(part)
        for idx, row in enumerate(rows):
            if self.item_is_needed(self.rows_ids, idx):
                self.download_row(dir_name, '%02d - %s' % ((idx + 1),
                                  row_names[idx].text.strip()), row)

    def download_row(self, dir_name, name, row):
        resources = self.get_resources(row)
        for resource in resources:
            if self.item_is_needed(self.types, resource[1]):
                self.download_resource(dir_name, name, resource)

    def download_resource(self, dir_name, name, resource):
        res_url = resource[0]
        res_type = resource[1]
        url, content_type = self.get_real_resource_info(res_url)
        ext = self.get_file_ext(url, content_type, res_type)
        filename = self.get_file_name(dir_name, name, ext)
        self.retrieve(url, filename)

    def retrieve(self, url, filename):
        if os.path.exists(filename) and not self.force:
            log("skipping file '%s'" % filename)
        else:
            log("downloading file '%s'" % filename)
            try:
                self.br.retrieve(url, filename)
            except KeyboardInterrupt:
                raise
            except:
                log("couldn't download the file")

    def item_is_needed(self, etalons, sample):
        return (len(etalons) == 0) or (sample in etalons)

    def get_file_name(self, dir_name, name, ext):
        name = self.escape_name(name)
        return ('%s.%s' % (os.path.join(dir_name, name), ext))

    def escape_name(self, name):
        name = name.replace('/', '_').replace('\\', '_')
        if ESCAPE_FILE_NAME:
            for c in ILLEGAL_CHARS:
                name = name.replace(c, '_')
        return name

    def get_real_resource_info(self, res_url):
        try:
            src = self.br.open(res_url)
            try:
                url = src.geturl()
                content_type = src.info().get('content-type', '')
                return (url, content_type)
            finally:
                src.close()
        except:
            return (res_url, '')

    def get_file_ext(self, url, content_type, res_type):
        m = REG_URL_FILE.search(url)
        if m:
            return m.group(2)
        m = REG_CONT_TYPE_EXT.match(content_type)
        if m:
            return m.group(1)
        return DEFAULT_EXT[res_type]

    def get_parts(self, doc):
        items = select(doc, 'ul.item_section_list')
        titles = select(doc, 'h3.list_header')
        return items, titles

    def get_rows(self, doc):
        rows = select(doc, 'div.item_resource')
        titles = select(doc, 'a.lecture-link')
        return rows, titles

    def get_resources(self, doc):
        resources = []
        for a in select(doc, 'a'):
            url = a.get('href')
            title = a.get('title').lower()
            resources.append((url, title))
        return resources


class GenericDownloader(object):
    @classmethod
    def downloader(cls, course):
        dl_name = course.capitalize() + 'Downloader'
        dl_bases = (CourseraDownloader,)
        dl_dict = dict(
            login_url=('https://www.coursera.org/%s/auth/auth_redirector' +
                       '?type=login&subtype=normal&email=') % course,
            home_url='https://class.coursera.org/%s/class/index' % course,
            lectures_url='https://class.coursera.org/%s/lecture/index' %
                         course,
            course_name=course)
        cls = type(dl_name, dl_bases, dl_dict)
        return cls


class DecrementAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        values = [value - 1 for value in values]
        setattr(namespace, self.dest, values)


class TypeReplacementAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        values = [TYPE_REPLACEMENT[value] if value in TYPE_REPLACEMENT.keys()
                else value for value in values]
        setattr(namespace, self.dest, values)


def create_arg_parser():
    parser = argparse.ArgumentParser(
        description="Downloads materials from Coursera.")
    parser.add_argument('course')
    parser.add_argument('-p', '--parts', action=DecrementAction,
                        nargs='*', default=[], type=int)
    parser.add_argument('-r', '--rows', action=DecrementAction,
                        nargs='*', default=[], type=int)
    parser.add_argument('-t', '--types', action=TypeReplacementAction,
                        nargs='*', default=[], choices=TYPES)
    parser.add_argument('-f', '--force', action='store_true')
    parser.add_argument('-v', '--verbose', action='count')
    return parser


def create_config(ns):
    config = dict()
    config['parts'] = ns.parts
    config['rows'] = ns.rows
    config['types'] = ns.types
    config['force'] = ns.force
    return config


def get_downloader_class(course):
    return GenericDownloader.downloader(course)


def main():
    global verbose
    arg_parser = create_arg_parser()
    ns = arg_parser.parse_args(sys.argv[1:])
    config = create_config(ns)
    verbose = ns.verbose
    dl_class = get_downloader_class(ns.course)
    dl = dl_class(config)
    dl.authenticate()
    dl.download()


def log(message):
    if verbose:
        print message

if __name__ == '__main__':
    main()
