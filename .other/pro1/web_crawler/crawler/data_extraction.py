from bs4 import BeautifulSoup
import json
import logging
logger = logging.getLogger(__name__)

def extract_data(soup: BeautifulSoup, extraction_rules):
    extracted_data = {}
    if not soup:
        logger.warning("No soup provided for data extraction")
        return extracted_data
    if not extraction_rules:
        return extracted_data
    try:
        for field_name, rule in extraction_rules.items():
            rule_type = rule.get('type', 'css')
            selector = rule.get('selector')
            attribute = rule.get('attribute')
            multiple = rule.get('multiple', False)

            if rule_type == 'css':
                elements = soup.select(selector)
            elif rule_type == 'xpath':
                elements = soup.find_all(xpath=selector)
            else:
                logger.warning(f"Unsupported extraction rule type: {rule_type}")
                continue
            if not elements:
                logger.debug(f"No element found for selector: {selector}")
                extracted_data[field_name] = None if not multiple else []
                continue
            if multiple:
                values = []
                for element in elements:
                    value = extract_value_from_element(element, attribute)
                    if value:
                        values.append(value)
                extracted_data[field_name] = values
            else:
                value = extract_value_from_element(elements[0], attribute)
                extracted_data[field_name] = value
        return extracted_data
    except Exception as e:
        logger.error(f"Error during data extraction: {e}")
        return {}

def extract_value_from_element(element, attribute):
    if attribute:
        return element.get(attribute)
    else:
        return element.text.strip()

def extract_json_data(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        script_tags = soup.find_all('script', type='application/ld+json')

        all_data = []
        for tag in script_tags:
            try:
                data = json.loads(tag.string)
                all_data.append(data)
            except json.JSONDecodeError:
                logger.debug(f"Skip decoding error for content: {tag.string}")
        return all_data
    except Exception as e:
        logger.error(f"Error extracting JSON-LD data: {e}")
        return []
        