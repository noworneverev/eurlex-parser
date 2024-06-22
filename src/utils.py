from bs4 import BeautifulSoup
import re

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