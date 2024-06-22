from collections import OrderedDict
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import re
import json
from src.utils import html_table_to_markdown
import pandas as pd
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

def parse_title(soup):
    title_text = ''
    tit_1_div = soup.find('div', id="tit_1")
    if tit_1_div:
        title_text = tit_1_div.text
        title_text = title_text.replace('\u00a0',' ').strip()
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
        elif key:
            results[key] = ''
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
                article_id = c.text.replace("\n", "").replace('\u00a0', ' ')
            elif c.name == 'div' and c.get('class') == ['eli-title']:
                article_title = c.text.replace("\n", "")                
            # elif c.findChildren == 'p' and "sti-art" in str(c.get('class')):
            #     article_title = c.text.replace("\n", "")
            else:                                                
                article_text += clean_text(c.text)
        
        article_text = article_text.lstrip('\n').rstrip('\n').replace('\n\n\n','\n')            
                    
        parent_info = find_parent_title(div.findParent("div"))
        parent_info = OrderedDict(reversed(list(parent_info.items())))
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

        parent_a = note.findParent('a')
        foot_note_id = parent_a['href'][1:] if parent_a and 'href' in parent_a.attrs else None
        foot_note = soup.find('a', id=foot_note_id) if foot_note_id else None

        note_dic['id'] = note.text
        note_text = ''
        if foot_note:
            parent_p = foot_note.findParent('p')
            if parent_p:
                note_text = parent_p.text
        cleaned_note_text = extract_note_text(note_text)
        note_dic['text'] = cleaned_note_text

        url = ''
        if foot_note and parent_p:
            a_tags = parent_p.find_all('a')
            if len(a_tags) >= 2:
                second_a_tag = a_tags[1]
                href = second_a_tag.get('href')
                if href:
                    index = href.find("legal-content")
                    url = "https://eur-lex.europa.eu/" + href[index:] if index != -1 else ''
        note_dic['url'] = url

        notes.append(note_dic)
    return notes


def extract_text_between(start_tag, end_tag=None, include_start_tag=False):
    """
    Function to extract the text between two tags
    """
    content = []
    if include_start_tag:
        content.append(start_tag.get_text(separator=" ", strip=True))          
    for element in start_tag.find_all_next():                
        if element == end_tag:
            break
        if element.get('class') and ('SectionTitle' in element.get('class') or 'ChapterTitle' in element.get('class')):
            continue
        if element.name == 'p':
            content.append(element.get_text(separator=" ", strip=True))            
            
    return "\n\n".join(content)

def extract_note_between(soup, start_tag, end_tag=None):
    notes = []
    for element in start_tag.find_all_next():
        note = {}
        if element == end_tag:
            break
        if element.get('class') and ('SectionTitle' in element.get('class') or 'ChapterTitle' in element.get('class')):
            continue
        if element.name == 'span' and element.get('class') == ['FootnoteReference']:
            note_id = element.get_text(separator=" ", strip=True)                    
            a_tag = element.find('a', class_='footnoteRef')
            if a_tag and 'href' in a_tag.attrs:
                note_ref_id = a_tag['href'][1:]  # Removing the leading '#'                                            
            footnote_soup = soup.find('dd', id=note_ref_id)             
            note_text = footnote_soup.get_text(separator=" ", strip=True)
            external_refs = footnote_soup.find_all('a', class_='externalRef')
            note['id'] = note_id
            note['text'] = note_text
            note['external_refs'] = [ref.get('href') for ref in external_refs if ref.get('href').startswith('http')]
            notes.append(note)
            
    return notes

def extract_annex_entry(entry):
    # Define the regular expression pattern for the annex entry
    annex_pattern = r'(ANNEX [IVXLCDM]+)\s+(.*)'    

    # Search for the annex entry (case-insensitive)
    match = re.search(annex_pattern, entry, re.IGNORECASE)    
    if match:
        annex_id = match.group(1).strip()
        annex_title = match.group(2).strip()
        
        return annex_id, annex_title
    else:
        return None, None

def extract_annexes_from_soup(soup):
    # Find all content wrappers
    content_wrappers = soup.find_all('div', class_='contentWrapper')
    
    # Initialize list to hold annexes
    annexes = []

    # Ensure there are multiple content wrappers
    if len(content_wrappers) > 1:
        second_content_wrapper = content_wrappers[1]
        annexetitre_ps = second_content_wrapper.find_all('p', class_='Annexetitre')
        end_tag = soup.find_all('div', class_='content')[-1]
        
        # Loop through annexetitre paragraphs and extract information
        for i in range(len(annexetitre_ps)):
            current_annexe = annexetitre_ps[i]
            annex_id_title = current_annexe.get_text(separator=" ", strip=True)
            annex_id, annex_title = extract_annex_entry(annex_id_title)
            
            # Determine the next tag to extract text until
            next_annexe = annexetitre_ps[i + 1] if i < len(annexetitre_ps) - 1 else end_tag
            annex_text = extract_text_between(current_annexe, next_annexe)
            
            annexes.append({
                "id": annex_id if annex_id else annex_id_title,
                "title": annex_title if annex_title else annex_id_title,
                "text": annex_text
            })
    
    return annexes

def extract_latest_chapter(sections):
    latest_chapter_index = -1
    
    for i, section in enumerate(sections):
        if section.lower().startswith('chapter'):
            latest_chapter_index = i
    
    if latest_chapter_index != -1 and latest_chapter_index + 1 < len(sections):
        return sections[:2] + sections[latest_chapter_index:latest_chapter_index + 2]
    else:
        return sections
    
def split_chapter_title(chapter_string):
    match = re.match(r'^(Chapter\s+\S+)\s+(.*)', chapter_string, re.IGNORECASE)
    if match:
        return [match.group(1), match.group(2)]
    else:
        return [chapter_string]  # return the original string if it doesn't match the pattern

def get_summary_by_celex_id(celex_id: str, language: str = "en") -> dict:
    """
    Support multiple languages
    """        
    url = f"https://eur-lex.europa.eu/legal-content/{language}/LSU/?uri=CELEX:{celex_id}"        
    response = requests.get(url)     

    soup = BeautifulSoup(response.text, 'lxml')

    # title
    title_h1 = soup.find("h1", class_="ti-main")
    title_text = title_h1.text if title_h1 else ''    

    # last modified    
    lastmod_div = soup.find('p', class_="lastmod")
    last_modified = lastmod_div.text.strip() if lastmod_div else ''
        
    chapter_contents = {}
    chapters = soup.find_all("h2", class_="ti-chapter")
    for chapter in chapters:
        chapter_title = chapter.text.strip()        

        content = []
        for sibling in chapter.find_next_siblings():
            if sibling.name == 'h2' and 'ti-chapter' in sibling.get('class', []) or 'lastmod' in sibling.get('class', []):
                break

            if sibling.name == 'ul':
                list_items = sibling.find_all('li')
                for item in list_items:
                    text = "- " + item.get_text().strip().replace('\xa0', '')
                    content.append(text)
            else:
                content.append(sibling.get_text().replace('\xa0', ''))
        
        chapter_contents[chapter_title] = '\n'.join(content)    

    return {
        'title': title_text,        
        'chapters': chapter_contents,
        'last_modified': last_modified
    }


def get_data_by_celex_id(celex_id: str, language: str = "en") -> dict:
    """
    Only support English for now
    """    

    url = f"https://eur-lex.europa.eu/legal-content/{language}/TXT/HTML/?uri=CELEX:{celex_id}"    
    response = requests.get(url)     
    soup = BeautifulSoup(response.text, 'lxml')

    if celex_id[5:7] == "PC":        
        return parse_pc_soup_data(soup)    
    else:        
        preamble = parse_pbl(soup)
        articles = parse_articles(soup)
        article_notes = [note for article in articles for note in article["notes"]]
            
        return {
            'title': parse_title(soup),
            'preamble': preamble,
            'articles': articles,
            'final_part': parse_fnp(soup),
            'notes': preamble["notes"] + article_notes,
            'annexes': parse_annexes(soup),
            'summary': get_summary_by_celex_id(celex_id, language)
        }

def parse_pc_soup_data(soup):
    title = ""
    statut = soup.find('p', class_='Statut')
    typedudocument_cp = soup.find('p', class_='Typedudocument_cp')
    titreobjet_cp = soup.find('p', class_='Titreobjet_cp')        
    title = "\n".join(filter(None, [statut.text if statut else '', 
                                            typedudocument_cp.text if typedudocument_cp else '', 
                                            titreobjet_cp.text if titreobjet_cp else '']))
        
    explantory_memorandum = {}
    explantory_memorandum_text = ""        
    start_tag = soup.find('p', class_='Exposdesmotifstitre')        
    end_tags = soup.find_all('p', class_='Statut')
    end_tag = end_tags[-1] if end_tags else None            
    explantory_memorandum_text = extract_text_between(start_tag, end_tag)      
    notes = extract_note_between(soup, start_tag, end_tag)   
    explantory_memorandum["text"] = explantory_memorandum_text
    explantory_memorandum["notes"] = notes        

    pbl = {}
    pbl_text = ""
    start_tag = soup.find('p', class_='Institutionquiagit')        
    end_tag = soup.find('p', class_='Formuledadoption')    
    pbl_text = extract_text_between(start_tag, end_tag, include_start_tag=True)
    notes = extract_note_between(soup, start_tag, end_tag)
    pbl["text"] = pbl_text
    pbl["notes"] = notes        
        
    articles = []
    metadata_stack = []

    # Find all <p> tags
    all_p_tags = soup.find_all('p')
    chapter_title = soup.find('p', class_='ChapterTitle')
    is_chapter_title_tag_exist = chapter_title is not None        

    # Traverse <p> tags and manage section titles
    for i, tag in enumerate(all_p_tags):
        if metadata_stack and tag.get_text(separator=" ", strip=True).lower().startswith("title"):
            metadata_stack = []

        if 'ChapterTitle' in tag.get('class', []):                
            title_text = tag.get_text(separator=" ", strip=True)
            metadata_stack = split_chapter_title(title_text)
                      
        if 'SectionTitle' in tag.get('class', []):
                # Update metadata stack with the latest section title                
            title_text = tag.get_text(separator=" ", strip=True)
            metadata_stack.append(title_text)   
            
        if 'Titrearticle' in tag.get('class', []):
                # Prepare current metadata from the stack     
            current_metadata = {}
            if is_chapter_title_tag_exist:           
                    # print(metadata_stack)
                current_metadata[metadata_stack[0]] = metadata_stack[1]
            else:
                metadata_stack = extract_latest_chapter(metadata_stack)                                    
                for j in range(0, len(metadata_stack), 2):
                    if j + 1 < len(metadata_stack):
                        current_metadata[metadata_stack[j]] = metadata_stack[j + 1]
                
                
                # Find the next article or end tag
            next_tag = None
            for j in range(i + 1, len(all_p_tags)):
                if 'Titrearticle' in all_p_tags[j].get('class', []) or 'Applicationdirecte' in all_p_tags[j].get('class', []):
                    next_tag = all_p_tags[j]
                    break
                
            article_text = extract_text_between(tag, next_tag)
            article_notes = extract_note_between(soup, tag, next_tag)
            article_id = tag.find('span').text.strip()
            article_title = tag.find('span').find_next_sibling().text.strip() if tag.find('span').find_next_sibling() else ''
            articles.append({
                    "id": article_id,
                    "title": article_title,
                    "text": article_text,
                    "notes": article_notes,
                    "metadata": current_metadata
                })
                    
    final_part = ""
    fait_text = soup.find('p', class_='Fait').get_text(separator=" ", strip=True)
    signature_text = soup.find('div', class_='signature').get_text(separator=" ", strip=True)
    final_part = fait_text + "\n" +  signature_text        
        
    financial_statement = {}
    finance_tag = soup.find('p', class_='Fichefinanciretitre') 
    footnote_tag = soup.find('dl', id='footnotes')    
    f = extract_text_between(finance_tag, footnote_tag)       
    f_notes = extract_note_between(soup, finance_tag, footnote_tag) 
    financial_statement["text"] = f
    financial_statement["notes"] = f_notes
        
        
    footnotes = soup.find('dl', id='footnotes')
    footnote_ids = [dd['id'] for dd in footnotes.find_all('dd')]
    notes = []        
    for footnote_id in footnote_ids:
        note = {}
        footnote_soup = soup.find('dd', id=footnote_id)
        note_text = footnote_soup.get_text(separator=" ", strip=True)
        external_refs = footnote_soup.find_all('a', class_='externalRef')            
        note_id = footnote_soup.find('span', class_='num').text.strip()
        note_id = re.search(r'\((\d+)\)', note_id).group(1)            
        note['id'] = note_id
        note['text'] = note_text
        note['external_refs'] = [ref.get('href') for ref in external_refs if ref.get('href').startswith('http')]
        notes.append(note)            
            
    annexes = extract_annexes_from_soup(soup)
    # return title,explantory_memorandum,notes,pbl,articles,final_part,financial_statement,annexes
    return {
            'title': title,
            'explantory_memorandum': explantory_memorandum,
            'preamble': pbl,
            'articles': articles,
            'final_part': final_part,
            'notes': notes,
            'annexes': annexes,
            'financial_statement': financial_statement
        }

def get_json_by_celex_id(celex_id) -> str:
    data = get_data_by_celex_id(celex_id)
    return json.dumps(data, indent=4)

def get_articles_by_celex_id(celex_id) -> pd.DataFrame:
    data = get_data_by_celex_id(celex_id)
    articles = data['articles']
    return pd.DataFrame(articles, columns=["id", "title", "text", "metadata", "notes"])