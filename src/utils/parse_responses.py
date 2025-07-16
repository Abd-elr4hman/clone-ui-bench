from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET


def extract_clone(response_message: str):
    """Extract HTML and CSS from text"""
    soup = BeautifulSoup(response_message, 'html.parser')
    body_tag = str(soup.find('body'))
    css_tag = str(soup.find('css'))  # Looks for <css> tags
    return {
        'body': body_tag,
        'css': css_tag
    }



def extract_score(response_message: str):
    """Extract score from text"""
    soup = BeautifulSoup(response_message, 'html.parser')
    score_xml_text = str(soup.find('score'))

    root = ET.fromstring(score_xml_text)
    score = int(root.text)
    
    return score
