import re
import os
import stat
import requests
import json
import urllib.request
import github3

from datetime import datetime as dt2

URL = os.getenv('PROF_GITHUB')
URI = URL.replace('https://github.com/', '')
OWNER, REPO = URI.split('/')
CONTENTS = f"https://api.github.com/repos/{URI}/contents/"
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
COMMIT_FILES = json.loads(os.getenv('COMMIT_FILES', "[]"))
COMMIT_TIME = os.getenv('COMMIT_TIME')
if COMMIT_TIME is None:
    COMMIT_TIME = dt2.now()
else:
    COMMIT_TIME = dt2.strptime(json.loads(COMMIT_TIME), "%Y-%m-%dT%H:%M:%SZ")
commit_time_string = COMMIT_TIME.strftime('%Y%m%d%H%M%S')
GRADER_EXEC = 'grader'

git = github3.GitHub(token=GITHUB_TOKEN)
repository = git.repository(OWNER, REPO)

PROF_WORKS = [r['name'] for r in requests.get(CONTENTS).json() if r['type'] == 'dir']
print(PROF_WORKS)
PROF_WORKS = repository.directory_contents('')
print(PROF_WORKS)
exit(1)

print(f'PROFESSOR GITHUB: {URI}')

graded = set()
scores = list()
for file in COMMIT_FILES:
    work = file.split('/')[0]
    if work == ".github":
        continue
    if work in graded:
        continue
    graded.add(work)
    if work not in PROF_WORKS:
        continue
    prof_files = {r['name']: r["download_url"] for r in requests.get(f'{CONTENTS}/{work}').json()}
    if 'due_to.txt' in prof_files:
        date = requests.get(prof_files['due_to.txt']).content
        date = re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', str(date, encoding='utf8'))
        del prof_files['due_to.txt']
        if date:
            date = dt2.strptime(date.group(0), "%Y-%m-%dT%H:%M:%S")
            if COMMIT_TIME > date:
                continue
    print(f'TASK: {work}')
    if len(prof_files) != 1:
        print('ERROR: invalid number of grader files (warn your professor)')
        continue
    curr = os.getcwd()
    os.chdir(work)
    urllib.request.urlretrieve(list(prof_files.values())[0], GRADER_EXEC)
    os.chmod(GRADER_EXEC, stat.S_IRWXU)
    os.system(f'./{GRADER_EXEC} > grader_{commit_time_string}.txt 2>&1')
    with open(f'grader_{commit_time_string}.txt', 'r') as log_file:
        log = log_file.read()
    os.remove(GRADER_EXEC)
    print(log)
    score = json.loads(log.strip().splitlines()[-1])
    score['task'] = work
    scores.append(score)
    os.chdir(curr)

print(json.dumps(scores))



