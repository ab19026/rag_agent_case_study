import sys, json
sys.path.append('..')

from observability.logger import 

def parse_json_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json
    except Exception as e:
        log("JSON_PARSE_EXCEPTION", e, path)


def load_file(path):
    try:
        rst = ''
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                rst += line + '\n'
        return rst
    except Exception as e:
        log("FILE_LOAD_EXCEPTION", e, path)

