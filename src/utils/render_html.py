import base64

def render(html_body:str, css:str):
    """Render HTML/CSS."""

    # check html and css are not empty
    if len(html_body) == 0 or len(css) == 0:
        raise ValueError("Invalid html or css. Must be a non empty string.")

    
    # Combine HTML and CSS
    full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <!-- The page is served as a base64 data URL, which carries no
                 charset, so without this the browser decodes our UTF-8 bytes as
                 windows-1252 and every em dash, curly quote and arrow renders
                 as mojibake. -->
            <meta charset="utf-8">
            <style>{css}</style>
        </head>
        <body>
            {html_body}
        </body>
        </html>
        """

    # Encode the HTML as base64 and create a data URL
    html_encoded = base64.b64encode(full_html.encode('utf-8')).decode('utf-8')
    data_url = f"data:text/html;base64,{html_encoded}"
    return data_url
    