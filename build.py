"""Build one .ts4script per fix into dist/.

Must run with Python 3.7 (the interpreter version used by The Sims 4), otherwise the
compiled bytecode will not load in game:

    py -3.7 build.py
"""
import os
import py_compile
import re
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'src')
DIST = os.path.join(ROOT, 'dist')
PREFIX = 'ts4_unofficial_fix_'

if sys.version_info[:2] != (3, 7):
    sys.exit('build.py must run with Python 3.7 (found {}.{})'.format(*sys.version_info[:2]))


def build_one(fix_file, common):
    with open(os.path.join(SRC, fix_file), encoding='utf-8') as f:
        body = f.read()
    fix_id = re.search(r"^FIX_ID = '([a-z0-9_]+)'", body, re.M).group(1)
    module = PREFIX + fix_id
    source = "FIX_ID = '{}'\n{}\n{}".format(fix_id, common, body)
    with tempfile.TemporaryDirectory() as tmp:
        py_path = os.path.join(tmp, module + '.py')
        pyc_path = os.path.join(tmp, module + '.pyc')
        with open(py_path, 'w', encoding='utf-8') as f:
            f.write(source)
        py_compile.compile(py_path, cfile=pyc_path, dfile=module + '.py', doraise=True)
        out = os.path.join(DIST, 'UnofficialFix_{}.ts4script'.format(fix_id))
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_STORED) as z:
            z.write(pyc_path, module + '.pyc')
    return out


def main():
    os.makedirs(DIST, exist_ok=True)
    with open(os.path.join(SRC, '_common.py'), encoding='utf-8') as f:
        common = f.read()
    for fix_file in sorted(os.listdir(SRC)):
        if fix_file.endswith('.py') and not fix_file.startswith('_'):
            print(build_one(fix_file, common))


if __name__ == '__main__':
    main()
