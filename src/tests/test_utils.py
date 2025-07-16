from src.utils.parse_responses import extract_clone
import htmlmin

def test_extract_clone():
    input_text = """
        Some text before
        <HTML>
            <body>
                <div style="background: lightblue; padding: 20px;">
                    <h1>Hello World</h1>
                    <p>This is rendered content</p>
                </div>
            </body>
        </HTML>
        Between sections
        <CSS>
        h1 { color: darkblue; text-align: center; }
        p { font-family: Arial; font-size: 18px; }
        </CSS>
        Text after
        """
    assert htmlmin.minify(extract_clone(input_text)["body"], remove_empty_space=True) == htmlmin.minify("""<body>
            <div style="background: lightblue; padding: 20px;">
                <h1>Hello World</h1>
                <p>This is rendered content</p>
            </div>
        </body>""",remove_empty_space=True)
    
