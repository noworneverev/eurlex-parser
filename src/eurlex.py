import requests
from bs4 import BeautifulSoup
import re
import json
from utils import html_table_to_markdown
import pandas as pd

def get_data_by_celex_id(celex_id: str, language: str = "en") -> dict:
    """
    Only support English for now
    """    

    url = f"https://eur-lex.europa.eu/legal-content/{language}/TXT/HTML/?uri=CELEX:{celex_id}"    
    response = requests.get(url)     

    soup = BeautifulSoup(response.text, 'lxml')
                       
    return {
        'title': parse_title(soup),
        'preamble': parse_pbl(soup),        
        'articles': parse_articles(soup),
        'final_part': parse_fnp(soup),
        'annexes': parse_annexes(soup)
    }

def parse_title(soup):
    title_text = ''
    tit_1_div = soup.find('div', id="tit_1")
    if tit_1_div:
        title_text = tit_1_div.text
        title_text = title_text.replace('\u00a0',' ')
    return title_text

def parse_fnp(soup):
    fnp_text = ''
    fnp_1_div = soup.find('div', id="fnp_1")
    if fnp_1_div:
        res = [line for line in fnp_1_div.text.split('\n') if line.strip()]
        res = '\n'.join(res)
        fnp_text = re.sub(r'(\(\d+\))\n', r'\1 ', res)
        fnp_text = fnp_text.replace('\u00a0',' ')
    return fnp_text

def parse_pbl(soup):
    pbl_text = ''
    pbl_1_div = soup.find('div', id="pbl_1") 
    if pbl_1_div:
        res = [line for line in pbl_1_div.text.split('\n') if line.strip()]
        res = '\n'.join(res)
        pbl_text = re.sub(r'(\(\d+\))\n', r'\1 ', res)
        pbl_text = pbl_text.replace('\u00a0',' ')

    notes = extract_notes(soup, pbl_1_div) 
                
    return {
        'text': pbl_text,
        'notes': notes
    }
        
def parse_annexes(soup):
    annexes = []
    divs_with_anx_id = soup.find_all("div", class_="eli-container", id=lambda x: x and x.startswith("anx"))
    for div in divs_with_anx_id:
        annex_data = {}      
        annex_id = ''
        annex_title = ''
        annex_text = ''
        annex_table = ''
        for c in div.children:
            if c.name == 'p' and "doc-ti" in str(c.get('class')):
                annex_id = c.text.strip()
            elif c.name == 'p' and "ti-grseq-1" in str(c.get('class')) and not annex_title:
                annex_title = c.text.strip()
            elif c.name == 'table' and "table" in str(c.get('class')):
                annex_table = html_table_to_markdown(str(c))                
            else:                                                
                annex_text += clean_text(c.text)
        
        annex_text = annex_text.lstrip('\n').rstrip('\n').replace('\n\n\n','\n')
        annex_data['id'] = annex_id
        annex_data['title'] = annex_title
        annex_data['text'] = annex_text
        annex_data['table'] = annex_table
        annexes.append(annex_data)
    return annexes

def clean_text(text):
    text = re.sub(r'\n{2,}', '\n', text)                                                                                
    text = re.sub(r'\n([a-z0-9]\))', r' \1', text)
    text = re.sub(r'\n(\d+\.\s+)', r' \1', text)
    text = re.sub(r'(\(\d+\))\n', r'\1 ', text)
    text = re.sub(r'(\s*\d+\.)\n', r'\1 ', text)
    text = re.sub(r'(\([a-z]\))\n', r'\1 ', text)
    text = re.sub(r'(\([IVXLCDM]+\))\n', r'\1 ', text)
    text = re.sub(r'(\([ivxlcdm]+\))\n', r'\1 ', text)
    text = text.replace('\n\n','')
    text = text.replace('\u00a0',' ')
    return text

def find_parent_title(div, depth=0, results=None):
        if results is None:
            results = {}
        if div is None or depth > 10:  # Avoid too deep recursion
            return results
        key, value = None, None
        for d in div.children:
            if d.name == 'p' and d.get('class') == ['oj-ti-section-1']:
                key = d.text.strip()
            elif d.name == 'div' and d.get('class') == ['eli-title']:
                value = d.text.strip()
        if key and value:
            results[key] = value
        parent_div = div.findParent("div")
        return find_parent_title(parent_div, depth + 1, results)

def parse_articles(soup):
    articles = []    
    # bottom up
    divs_with_art_id = soup.find_all("div", class_="eli-subdivision", id=lambda x: x and x.startswith("art"))
    for i, div in enumerate(divs_with_art_id):        
        notes = extract_notes(soup, div)        
        article_data = {}                
        article_id = ''
        article_title = ''
        article_text = ''        
        for c in div.children:
            if c.name == 'p' and "ti-art" in str(c.get('class')):
                article_id = c.text.replace("\n", "")
            elif c.name == 'div' and c.get('class') == ['eli-title']:
                article_title = c.text.replace("\n", "")                
            # elif c.findChildren == 'p' and "sti-art" in str(c.get('class')):
            #     article_title = c.text.replace("\n", "")
            else:                                                
                article_text += clean_text(c.text)
        
        article_text = article_text.lstrip('\n').rstrip('\n').replace('\n\n\n','\n')            
                    
        parent_info = find_parent_title(div.findParent("div"))
        article_data['id'] = article_id
        article_data['title'] = article_title
        article_data['text'] = article_text
        article_data['metadata'] = parent_info
        article_data['notes'] = notes
        articles.append(article_data)
    return articles

def extract_note_text(text):
    cleaned_text = text.strip().replace('\xa0', '')
    cleaned_text = re.sub(r'^\(\d+\)\s+', '', cleaned_text)    
    cleaned_text = re.sub(r'^\(\d+\)', '', cleaned_text)
    cleaned_text = re.sub(r'^\(\*\d+\)', '', cleaned_text)
    return cleaned_text.strip()

def extract_notes(soup, div):
    note_tags = div.find_all('span', class_='oj-super oj-note-tag') if div else []    
    notes = []

    for note in note_tags:
        note_dic = {}          
        
        foot_note_id = note.findParent('a')['href'][1:]
        foot_note = soup.find('a', id=foot_note_id)

        note_dic['id'] = note.text
        note_text = foot_note.findParent('p').text
        cleaned_note_text = extract_note_text(note_text)
        note_dic['text'] = cleaned_note_text
        
        url = ''
        a_tags = foot_note.findParent('p').find_all('a')        
        if len(a_tags) >= 2:
            second_a_tag = a_tags[1]
            href = second_a_tag.get('href')
            index = href.find("legal-content")
            url = "https://eur-lex.europa.eu/" + href[index:]
        note_dic['url'] = url     
        notes.append(note_dic)
    return notes


def get_json_by_celex_id(celex_id) -> str:
    data = get_data_by_celex_id(celex_id)
    return json.dumps(data, indent=4)

def get_articles_by_celex_id(celex_id) -> pd.DataFrame:
    data = get_data_by_celex_id(celex_id)
    articles = data['articles']
    return pd.DataFrame(articles, columns=["id", "title", "text", "metadata", "notes"])
    
    

# data = get_data_by_celex_id('32013R0575')

# df = get_articles_by_celex_id('32013R0575')
# df.head(5)

with open('32013L0036.json', 'w', encoding='utf-8') as f:
    f.write(get_json_by_celex_id('32013L0036'))

with open('32013R0575.json', 'w', encoding='utf-8') as f:
    f.write(get_json_by_celex_id('32013R0575'))

with open('32019L0878.json', 'w', encoding='utf-8') as f:
    f.write(get_json_by_celex_id('32019L0878'))

with open('32019R0876.json', 'w', encoding='utf-8') as f:
    f.write(get_json_by_celex_id('32019R0876'))

# with open('de.json', 'w', encoding='utf-8') as f:
#     f.write(json.dumps(get_html_by_celex_id('32013R0575', 'de'), indent=4))

# with open('en.json', 'w', encoding='utf-8') as f:
#     f.write(json.dumps(get_data_by_celex_id('32013R0575'), indent=4))

# get_html_by_celex_id('32013R0575', 'fr')


# with open('32013L0036.json', 'w', encoding='utf-8') as f:
#     f.write(get_html_by_celex_id('32013L0036'))

# with open('32019L0878.json', 'w', encoding='utf-8') as f:
#     f.write(get_html_by_celex_id('32019L0878'))

# with open('32019R0876.json', 'w', encoding='utf-8') as f:
#     f.write(get_html_by_celex_id('32019R0876'))


# get_html_by_celex_id('32013R0575')