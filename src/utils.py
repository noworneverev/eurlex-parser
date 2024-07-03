from bs4 import BeautifulSoup
import re
from typing import List

def html_table_to_markdown(html):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')

    if not table:
        raise ValueError("No table found in the provided HTML")

    headers = []
    rows = []

    # Extract headers
    header_row = table.find('tr')
    if header_row:
        for th in header_row.find_all('th'):
            headers.append(th.get_text().strip())

    # Extract rows
    for tr in table.find_all('tr'):
        row = []
        for td in tr.find_all(['td', 'th']):
            row.append(td.get_text().strip())
        if row:
            rows.append(row)

    # Determine the number of columns
    num_columns = len(headers) if headers else max(len(row) for row in rows)

    # Ensure all rows have the correct number of columns
    for row in rows:
        while len(row) < num_columns:
            row.append('')

    # Determine the column widths
    column_widths = [0] * num_columns
    for i, header in enumerate(headers):
        column_widths[i] = len(header)
    for row in rows:
        for i, cell in enumerate(row):
            column_widths[i] = max(column_widths[i], len(cell))

    # Create the Markdown table
    def format_row(row):
        return '| ' + ' | '.join(f"{cell:<{column_widths[i]}}" for i, cell in enumerate(row)) + ' |'

    markdown = []
    if headers:
        markdown.append(format_row(headers))        
    else:
        # first row as header        
        markdown.append(format_row(rows[0]))

    markdown.append('|' + '|'.join('-' * (width + 2) for width in column_widths) + '|')

    if not headers:
        rows = rows[1:]
    
    for row in rows:
        markdown.append(format_row(row))

    return '\n'.join(markdown)

def extract_directive_and_regulation_at_beginning(text: str) -> str:
    # General pattern to match directives and regulations    
    pattern = (
        r'(^\s*\(?\d{0,3}\)?\s*Directive \d+/\d+/\s?\w{2,3})|'
        r'(^\s*\(?\d{0,3}\)?\s*Directive \(\w{2,3}\) \d+/\d+)|'
        r'(^\s*\(?\d{0,3}\)?\s*Regulation \(\w{2,3}\) No \d+/\d+)|'
        r'(^\s*\(?\d{0,3}\)?\s*Council Regulation \(\w{2,3}\) No \d+/\d+)|'
        r'(^\s*\(?\d{0,3}\)?\s*Regulation \(\w{2,3}\) \d+/\d+)|'
        r'(^\s*\(?\d{0,3}\)?\s*Decision \d+/\d+/\w{2,3})|'
        r'(^\s*\(?\d{0,3}\)?\s*Commission Recommendation \d+/\d+/\w{2,3})|'
        r'(^\s*\(?\d{0,3}\)?\s*Regulation \d+/\d+)'
    )

    match = re.match(pattern, text, re.IGNORECASE)
    
    if match:
        directive = match.group(0).strip()        
        directive = re.sub(r'^\s*\(?\d{0,3}\)?\s*', '', directive)        
        return directive
    return None


def extract_directives_and_regulations(text: str) -> List[str]:
    # General pattern to match directives and regulations
    pattern = (
        r'(Directive \d+/\d+/\s?\w{2,3})|'
        r'(Directive \(\w{2,3}\) \d+/\d+)|'
        r'(Regulation \(\w{2,3}\) No \d+/\d+)|'
        r'(Regulation \(\w{2,3}\) \d+/\d+)|'
        r'(Decision \d+/\d+/\w{2,3})|'
        r'(Commission Recommendation \d+/\d+/\w{2,3})|'
        r'(Regulation \d+/\d+)'
    )

    matches = re.findall(pattern, text, re.IGNORECASE)
    results = [match for group in matches for match in group if match]
    unique_results = list(dict.fromkeys(results))
    
    # For case like "Directives 2014/24/EU, 2014/25/EU or 2014/23/EU"
    directive_pattern = r'Directives?\s+((?:\d{4}/\d+/\w{2,3}\s*(?:, )?)+)\s*or\s+(\d{4}/\d+/\w{2,3})'
    directive_matches = re.findall(directive_pattern, text, re.IGNORECASE)

    if directive_matches:
        combined_directives = ', '.join(directive_matches[0])
        items = combined_directives.split(', ')
        directives_list = ['Directive ' + item.strip() for item in items if item]
        unique_results.extend(directives_list)
        unique_results = list(dict.fromkeys(unique_results))

    
    # For case like "Directives 2014/24/EU or 2014/25/EU"    
    directive_pattern = r'Directives? (\d{4}/\d+/\w{2,3})(?:, (\d{4}/\d+/\w{2,3}))* (?:and|or) (\d{4}/\d+/\w{2,3})'

    directive_matches = re.findall(directive_pattern, text, re.IGNORECASE)    
    directives_list = []
    if directive_matches:        
        all_matches = [match for sublist in directive_matches for match in sublist if match]
        directives_list = ['Directive ' + item.strip() for item in all_matches]
        unique_results.extend(directives_list)
        unique_results = list(dict.fromkeys(unique_results))
    
    # For case like "Regulations (EU) No 2016/679 or (EU) No 2016/680"
    # regulation_pattern = r'Regulations? \(EU\) No (\d{4}/\d+)(?:, \(EU\) No (\d{4}/\d+))* or \(EU\) No (\d{4}/\d+)'
    regulation_pattern = r'Regulations? \(EU\) No (\d{3,4}/\d+)(?:, \(EU\) No (\d{3,4}/\d+))* (?:and|or) \(EU\) No (\d{3,4}/\d+)'
    regulation_matches = re.findall(regulation_pattern, text, re.IGNORECASE)

    if regulation_matches:
        all_matches = [match for sublist in regulation_matches for match in sublist if match]
        regulations_list = ['Regulation (EU) No ' + item.strip() for item in all_matches]
        unique_results.extend(regulations_list)
        unique_results = list(dict.fromkeys(unique_results))

    return unique_results