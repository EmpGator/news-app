import os

import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader


class BaseParser:
    parser = "html.parser"
    def __init__(self, url, output='test.html'):
        self.header = ''
        self.subheader = ''
        self.content = []
        self.always_visible_content = []
        self.rest_of_content = []
        self.success = False
        r = requests.get(url)
        self.code = r.status_code
        if r.status_code != 200:
            print(f'Status code: {r.status_code}')
            return
        self.soup = BeautifulSoup(r.text, self.parser)
        self.parse_header()
        self.parse_content()
        if len(self.content) >= 3:
            self.split_content()
        else:
            self.rest_of_content = self.content

    def split_content(self):
        divider = int(len(self.content)/3)
        self.always_visible_content = self.content[:divider]
        self.always_visible_content[-1] = self.always_visible_content[-1].replace(
            '<p>', '<p {% if not paywall.show %} class="paytext" {% endif %}>', 1)
        self.rest_of_content = self.content[divider:]

    def trim_text(self, text):
        text = self.split_and_filter_text(text)
        return '\n'.join(text)

    def split_and_filter_text(self, text):
        return [i for i in text.split('\n') if i]

    def parse_header(self):
        pass

    def parse_content(self):
        pass

    def get_content(self):
        if all((self.header, self.content)):
            return self.header, self.subheader, self.always_visible_content, self.rest_of_content
        return []

    def create_test_file(self):
        with open('test.html', 'w') as f:
            print(f'<h1>{self.header}</h1>', file=f)
            if self.subheader:
                print(f'<h2>{self.subheader}</h2>', file=f)
            for line in self.content:
                print(line, file=f)


class GuardianParser(BaseParser):

    def __init__(self, url, output='test.html'):
        super().__init__(url, output=output)


    def parse_header(self):
        for header in self.soup.find_all('header', class_='content__head'):
            for h1 in header.find_all('h1', class_='content__headline',limit=1):
                self.header = h1.text.strip()
            for header_div in header.find_all('div', class_='content__standfirst'):
                self.subheader = header_div.text.strip()

    def parse_content(self):
        contents = []
        for div in self.soup.find_all('div', class_='content__article-body'):
            for child in div.children:
                if child.name == 'p':
                    contents.append(str(child))
                if child.name == 'figure':
                    try:
                        for div in child.find_all('div'):
                            # div.attrs.get if below doesnt work
                            if 'block-share' in div.get('class', []):
                                div.extract()
                            div['style'] = None
                        [i.extract() for i in child.find_all('span')]
                        contents.append(str(child))
                    except:
                        pass
        self.content = contents


class PoliticoParser(BaseParser):


    def parse_header(self):
        for h2 in self.soup.find_all('h2'):
            self.header = h2.text.strip()
        p = self.soup.find('p', class_='dek')
        self.subheader = p.text.strip()

    def parse_content(self):
        for figure in self.soup.find_all('figure', class_='art'):
            self.content.append(str(figure))
            break
        for div in self.soup.find_all('div', class_='story-text'):
            for child in div.children:
                if child.name in ['p', 'figure']:
                    self.content.append(str(child))


class TheVergeParser(BaseParser):

    def parse_header(self):
        for h1 in self.soup.find_all('h1'):
            self.header = h1.text.strip()
        p = self.soup.find('p', class_='p-dek')
        self.subheader = p.text.strip()

    def parse_content(self):
        figure = self.soup.find('figure', class_='e-image')
        self.content.append(str(figure)) if figure else None
        div = self.soup.find('div', class_='c-entry-content')
        for child in div.children:
            if child.name in ['p', 'figure']:
                self.content.append(str(child))


class EngadgetParser(BaseParser):

    def parse_header(self):
        h1 = self.soup.find('h1', class_='t-h4@m-')
        self.header = h1.text.strip()
        div = self.soup.find('div', class_='t-d7@m-')
        self.subheader = div.text.strip()

    def parse_content(self):
        div = self.soup.find('div', id='page_body')
        for child in div.descendants:
            if child.name in ['p', 'img', 'image']:
                if child.get('alt', '').lower() not in ['share', 'like', 'comment']:
                    self.content.append(str(child))


class UsaTodayParser(BaseParser):

    def parse_header(self):
        h1 = self.soup.find('h1', class_='title')
        self.header = h1.text.strip()

    def parse_content(self):
        div = self.soup.find('div', class_='article-wrapper')
        for child in div.children:
            if child.name in ['p', 'h2']:
                self.content.append(str(child))
            if child.name == 'div' and 'asset-image' in child.get('class', ''):
                self.content.append(str(child))


class SpiegelParser(BaseParser):

    def parse_header(self):
        for header_tag in self.soup.findAll('header'):
            header = header_tag.find('span', class_='align-middle')
            if not header:
                continue
            self.header = header.text.strip()
            subheader = header_tag.find('div', class_='RichText')
            if subheader:
                self.subheader = subheader.text.strip()
            break

    def parse_content(self):
        article = self.soup.find('article')
        div = article.find('div', class_='relative')
        for child in div.descendants:
            if child.name in ['p']:
                self.content.append(str(child))
            if child.name in ['figure']:
                for button in child.find_all('button'):
                    button.extract()
                self.content.append(str(child))



class SfgateParser(BaseParser):

    def parse_header(self):
        div = self.soup.find('div', class_='article-content')
        header = div.find('h1')
        if header:
            self.header = header.text.strip()

    def parse_content(self):
        div = self.soup.find('div', class_='article-body')
        for child in div.descendants:
            if child.name in ['p', 'figure', 'img']:
                self.content.append(str(child))


class DailyMailParser(BaseParser):

    def parse_header(self):
        div = self.soup.find('div', class_='article-text')
        header = div.find('h2')
        if header:
            self.header = header.text.strip()

    def parse_content(self):
        div = self.soup.find('div', itemprop='articleBody')
        for child in div.descendants:
            if child.name in ['p', 'figure', 'img']:
                self.content.append(str(child))


class StuffParser(BaseParser):

    def parse_header(self):
        div = self.soup.find('div', class_='sics-component__news-page__container')
        header = div.find('h1')
        if header:
            self.header = header.text.strip()

    def parse_content(self):
        div = self.soup.find('div', class_='sics-component__story')
        for child in div.descendants:
            if child.name in ['p']:
                self.content.append(str(child))


class BbcParser(BaseParser):

    def parse_header(self):
        pass

    def parse_content(self):
        pass

if __name__ == '__main__':
    urls = [
        'https://www.bbc.com/sport/football/52972621'
    ]

    for url in urls:
        StuffParser(url).create_test_file()
