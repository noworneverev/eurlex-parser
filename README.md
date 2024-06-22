# Eurlex Parser

This Python package fetches and parses data(regulations, directives and proposals) from Eurlex, the official website for European Union law. It extracts various parts of legal documents by their CELEX IDs and supports exporting the data in JSON and Pandas DataFrame formats.

## Installation

```bash
pip install eurlex-parser
```

## Usage

### Functions

- `get_data_by_celex_id(celex_id: str, language: str = "en") -> dict`: Fetches and parses the data for the given CELEX ID. Returns a dictionary with the document's title, preamble, articles, final part, and annexes.
  
- `get_json_by_celex_id(celex_id: str) -> str`: Fetches and parses the data for the given CELEX ID and returns it in JSON format.

- `get_articles_by_celex_id(celex_id: str) -> pd.DataFrame`: Fetches and parses the articles for the given CELEX ID and returns them as a Pandas DataFrame.

- `get_summary_by_celex_id(celex_id: str, language: str = "en")` -> dict: Fetches and parses the summary for the given CELEX ID and returns it as a dictionary containing the document's title, chapters, and the last modified date. (Note: The summary is not available for all documents.)

### Examples

Following are some examples of how to use the functions to fetch and parse data from a CELEX ID. For example, the CELEX ID `32013R0575` corresponds to the following URL: https://eur-lex.europa.eu/legal-content/en/TXT/?uri=celex:32013R0575
1. Fetch and print data for a given CELEX ID:
    ```python
    from eurlex import get_data_by_celex_id

    data = get_data_by_celex_id('32013R0575')
    print(data)
    ```

2. Save data as a JSON file:
    ```python
    from eurlex import get_json_by_celex_id

    json_data = get_json_by_celex_id('32013R0575')
    with open('32013R0575.json', 'w', encoding='utf-8') as f:
        f.write(json_data)
    ```

3. Load articles into a Pandas DataFrame:
    ```python
    from eurlex import get_articles_by_celex_id

    df = get_articles_by_celex_id('32013R0575')
    print(df.head())
    ```
4. Fetch and print summary for a given CELEX ID:
    ```python
    from eurlex import get_summary_by_celex_id

    summary = get_summary_by_celex_id('32013R0575')
    print(summary)
    ```


You can find some generated JSON files in the `examples` directory.

### Data Structure

The main data structure returned by `get_data_by_celex_id` is a dictionary with the following format:
```json
{
  "title": "Document Title",
  "preamble": {
    "text": "Preamble text",
    "notes": [
      {
        "id": "1",
        "text": "Note text",
        "url": "https://eur-lex.europa.eu/..."
      }
    ]
  },
  "articles": [
    {
      "id": "Article ID",
      "title": "Article Title",
      "text": "Article text",
      "metadata": {
        "parent_title1": "Parent Title 1",
        "parent_title2": "Parent Title 2",
      },
      "notes": [
        {
          "id": "1",
          "text": "Note text",
          "url": "https://eur-lex.europa.eu/..."
        }
      ]
    }
  ],
  "notes": [
    {
      "id": "1",
      "text": "Note text",
      "url": "https://eur-lex.europa.eu/..."
    }
  ],
  "final_part": "Final part text",
  "annexes": [
    {
      "id": "Annex ID",
      "title": "Annex Title",
      "text": "Annex text",
      "table": "Markdown table text"
    }
  ],
  "summary": {
    "title": "Document Title",
    "chapters": {
      "Chapter Title 1": "Chapter content 1",
      "Chapter Title 2": "Chapter content 2"
    },
    "last_modified": "Last modified date"
  }
}
```

### Notes

- The script currently supports fetching data in English (`en`) only.

## License

This project is licensed under the MIT License.