from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET


def extract_clone(response_message: str):
    """Extract HTML and CSS from text

    Returns None for a field when its block is absent, so callers can record a
    format failure instead of rendering the literal string "None".
    """
    soup = BeautifulSoup(response_message, 'html.parser')
    body_tag = soup.find('body')
    css_tag = soup.find('css')
    return {
        'body': str(body_tag) if body_tag is not None else None,
        # decode_contents() strips the <css> wrapper. Keeping it would leave
        # "<css>" glued to the first selector inside <style>, making that rule
        # invalid and silently discarding it.
        'css': css_tag.decode_contents() if css_tag is not None else None,
    }


def extract_score(response_message: str):
    """Extract score from text"""
    soup = BeautifulSoup(response_message, 'html.parser')
    score_xml_text = str(soup.find('score'))

    root = ET.fromstring(score_xml_text)
    score = int(root.text)
    
    return score
