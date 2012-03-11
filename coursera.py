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


REG_URL_FILE = re.compile(r'.*/([^./]+)\.([\w\d]+)$', re.I)
REG_CONT_TYPE_EXT = re.compile(r'^.*/([\d\w]+)$', re.I)
REG_TXT_RES = re.compile(r'^(.*format)=txt$', re.I)
TYPES = ('pdf', 'ppt', 'txt', 'movie')

# This dictionary is needed for not changing program interface
# every time Coursera changes type icon names.
TYPE_REPLACEMENT = {'movie': 'download'}
DEFAULT_EXT = {'pdf': 'pdf', 'ppt': 'ppt', 'txt': 'txt', 'download': 'mp4'}


class CourseraDownloader(object):
    login_url = ''
    lectures_url = ''

    def __init__(self, parts_ids=[], rows_ids=[], types=[]):
        self.parts_ids = parts_ids
        self.rows_ids = rows_ids
        self.types = types
        self.br = Browser()
        self.br.set_handle_robots(False)

    def authenticate(self):
        self.br.open(self.login_url)
        self.br.form = self.br.forms().next()
        self.br['email'] = EMAIL
        self.br['password'] = PASSWORD
        self.br.submit()

    def download(self):
        page = self.br.open(self.lectures_url)
        doc = BeautifulSoup(page)
        parts = self.get_parts(doc)
        for idx, part in enumerate(parts):
            if self.item_is_needed(self.parts_ids, idx):
                self.download_part('%02d' % (idx + 1), part)

    def download_part(self, dir_name, part):
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
        rows = self.get_rows(part)
        for idx, row in enumerate(rows):
            if self.item_is_needed(self.rows_ids, idx):
                self.download_row(dir_name, '%02d' % (idx + 1), row)

    def download_row(self, dir_name, name, row):
        resources = self.get_resources(row)
        for resource in resources:
            if self.item_is_needed(self.types, resource[1]):
                self.download_resource(dir_name, name, resource)

    def item_is_needed(self, etalons, sample):
        return (len(etalons) == 0) or (sample in etalons)

    def download_resource(self, dir_name, name, resource):
        res_url = resource[0]
        res_type = resource[1]
        url, content_type = self.get_real_resource_info(res_url)
        ext = self.get_file_ext(url, content_type, res_type)
        filename = self.get_file_name(dir_name, name, ext)
        self.br.retrieve(url, filename)

        # Download subtitles in .srt format together with .txt.
        if res_type == 'txt':
            m = REG_TXT_RES.match(url)
            if m:
                ext = 'srt'
                url = '%s=%s' % (m.group(1), ext)
                filename = self.get_file_name(dir_name, name, ext)
                try:
                    self.br.retrieve(url, filename)
                except:
                    # Ignore if there is no subtitles in .srt format.
                    pass

    def get_file_name(self, dir_name, name, ext):
        return ('%s.%s' % (os.path.join(dir_name, name), ext)).lower()

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
        return select(doc, 'ul.item_section_list')

    def get_rows(self, doc):
        return select(doc, 'div.item_resource')

    def get_resources(self, doc):
        resources = []
        for a in select(doc, 'a'):
            url = a.get('href')
            img = select(a, 'img[src]')[0]
            src = img.get('src')
            f_type = REG_URL_FILE.search(src).group(1).lower()
            resources.append((url, f_type))
        return resources


class SaasDowloader(CourseraDownloader):
    login_url = ('https://www.coursera.org/saas/auth/auth_redirector' +
                 '?type=login&subtype=normal&email=')
    lectures_url = 'https://www.coursera.org/saas/lecture/index'


class NlpDownloader(CourseraDownloader):
    login_url = ('https://www.coursera.org/nlp/auth/auth_redirector' +
                 '?type=login&subtype=normal&email=')
    lectures_url = 'https://www.coursera.org/nlp/lecture/index'


class DecrementAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        values = [value - 1 for value in values]
        setattr(namespace, self.dest, values)


class TypeReplacementAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        values = [TYPE_REPLACEMENT[value] if value in TYPE_REPLACEMENT.keys()
                  else value for value in values ]
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
    return parser


def get_downloader_class(course):
    if course == 'saas':
        return SaasDowloader
    elif course == 'nlp':
        return NlpDownloader
    else:
        raise ValueError("Unknown course - %s." % course)


def test_parser():
    dl = CourseraDownloader()
    with open('test.html') as f:
        doc = BeautifulSoup(f)
        parts = dl.get_parts(doc)
        for part in parts:
            rows = dl.get_rows(part)
            for row in rows:
                resources = dl.get_resources(row)
                for resource in resources:
                    print resource


def main():
    arg_parser = create_arg_parser()
    ns = arg_parser.parse_args(sys.argv[1:])
    dl_class = get_downloader_class(ns.course)
    dl = dl_class(ns.parts, ns.rows, ns.types)
    dl.authenticate()
    dl.download()


if __name__ == '__main__':
    main()
