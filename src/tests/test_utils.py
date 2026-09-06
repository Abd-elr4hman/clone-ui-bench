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
    


def test_extract_clone_css_has_no_wrapper_tags():
    """The <css> wrapper must not survive into the stylesheet, or it would glue
    itself to the first selector and silently invalidate the first rule."""
    css = extract_clone("""
        <HTML><body><h1>Hi</h1></body></HTML>
        <CSS>
        h1 { color: darkblue; }
        p { font-size: 18px; }
        </CSS>
        """)["css"]

    assert "<css>" not in css.lower()
    assert "</css>" not in css.lower()
    assert css.strip().startswith("h1 {")


def test_extract_clone_returns_none_when_blocks_missing():
    result = extract_clone("Sorry, I cannot clone that interface.")

    assert result["body"] is None
    assert result["css"] is None
