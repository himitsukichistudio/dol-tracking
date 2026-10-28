"""Send the daily sponsored-post report for URLs newly added to index.html."""
import json, os, re, smtplib, sys
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate, make_msgid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, 'reported.json')

def load_rows():
    html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    m = re.search(r'W15=(\[.*?\]\]);', html, re.S)
    return json.loads(m.group(1))

def main():
    rows = load_rows()
    reported = set(json.load(open(STATE, encoding='utf-8'))) if os.path.exists(STATE) else set()
    if '--init' in sys.argv:
        urls = sorted({r[3] for r in rows if r[3]} | reported)
        json.dump(urls, open(STATE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('initialized', len(urls)); return
    force = os.environ.get('FORCE_TEST') == 'true'
    new = [r for r in rows if r[3] and r[3] not in reported]
    if force:
        new = [r for r in rows if r[3]][-2:]
        os.environ['REPORT_MODE'] = 'test'
    if not new:
        print('no new posts'); return

    blocks = '\n\n'.join(f'DOL name：{r[0]}\nSNS source：{r[1]}\nPost date：{r[2]}\nURL：{r[3]}' for r in new)
    body = ('ソレンセン様\n\nお世話になっております。\n'
            'スポンサード投稿にアップデートがございましたので、ご報告いたします。\n\n'
            f'{blocks}\n\nPosts URL：\nhttp://tracking.himitsukichistudio.com/\n\n'
            'ご確認のほど、よろしくお願いいたします。\n\n三浦')

    user = os.environ['GMAIL_USER']
    live = os.environ.get('REPORT_MODE', '') != 'test'
    to = ['nsoe@novonordisk.com'] if live else [user]
    cc = ['hiym@novonordisk.com', 'NBKO@novonordisk.com', 'YHTS@novonordisk.com',
          'OIHM@novonordisk.com', 'EKSV@novonordisk.com', 'kafw@novonordisk.com'] if live else []
    bcc = [user] if live else []

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = Header('進捗報告【スポンサード投稿 Wave1.5】', 'utf-8')
    msg['From'] = formataddr((str(Header('Keita Miura', 'utf-8')), user))
    msg['To'] = ', '.join(to)
    if cc: msg['Cc'] = ', '.join(cc)
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid(domain=user.split('@')[1])
    ref = os.environ.get('THREAD_MESSAGE_ID', '').strip()
    if ref:
        msg['In-Reply-To'] = ref
        msg['References'] = ref

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
        s.login(user, os.environ['GMAIL_APP_PASSWORD'])
        s.sendmail(user, to + cc + bcc, msg.as_string())
    print('sent', len(new), 'posts', 'LIVE' if live else 'TEST')

    if force:
        return
    reported |= {r[3] for r in new}
    json.dump(sorted(reported), open(STATE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main()
