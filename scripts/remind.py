"""Remind Miura of today's expected posts whose URLs are not yet on the tracking page."""
import datetime as dt, json, os, re, smtplib
from email.mime.text import MIMEText
from email.header import Header

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONTHS = {m: i for i, m in enumerate(['January','February','March','April','May','June','July',
          'August','September','October','November','December'], 1)}

def parse(d):
    m = re.match(r'(\d+)\w*\s+(\w+)\s+(\d{4})', d)
    return dt.date(int(m.group(3)), MONTHS[m.group(2)], int(m.group(1))) if m else None

def main():
    html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    rows = json.loads(re.search(r'W15=(\[.*?\]\]);', html, re.S).group(1))
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date()
    due = [r for r in rows if parse(r[2]) == today]
    missing = [r for r in due if not r[3]]
    if not missing:
        print('nothing missing'); return
    lines = '\n'.join(f'・{r[0]}（{r[1]}）' for r in missing)
    body = (f'本日（{today.month}/{today.day}）は下記の投稿予定がありますが、トラッキングページにURLがまだ入っていません。\n\n'
            f'{lines}\n\n投稿を確認できたら、URLをClaudeに送ってください。\n'
            '翌朝7:00の報告メールには、それまでに登録されたURLが入ります。')
    user = os.environ['GMAIL_USER']
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = Header(f'【URL未登録】本日の投稿 {len(missing)}件', 'utf-8')
    msg['From'] = user
    msg['To'] = user
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
        s.login(user, os.environ['GMAIL_APP_PASSWORD'])
        s.sendmail(user, [user], msg.as_string())
    print('reminded', len(missing))

if __name__ == '__main__':
    main()
