def clean_path_for_saving(path):
    relative_path = path.split('data', 1)[1].replace('\\', '/').lstrip('/')
    relative_path = 'data/' + relative_path
    return relative_path