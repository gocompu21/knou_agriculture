# -*- coding: utf-8 -*-
"""학습 자료(GisaResource)의 주소를 읽어 제목·출처·영상 id 를 뽑는다.

**API 키가 필요 없다.** 유튜브는 oEmbed 엔드포인트가 제목·채널명·썸네일을 그냥
돌려주고, 블로그는 <title> 만 가져오면 된다. 그래서 관리 화면에서 주소만
붙여넣으면 나머지 칸이 채워진다.

**바깥 주소를 서버가 가져오는 일이므로 도메인을 막는다.** 잡초 카드 사진에서
겪은 것과 같은 SSRF 통로다 — 아무 주소나 받아 주면 사내망이나 클라우드
메타데이터(169.254.169.254)를 긁어 오게 시킬 수 있다. 유튜브 oEmbed 는 유튜브
도메인만, 블로그 제목 읽기는 사설·예약 대역을 막는다.
"""
import ipaddress
import json
import re
import socket
import urllib.parse
import urllib.request

UA = 'Mozilla/5.0 (compatible; hanulstudy/1.0)'
TIMEOUT = 6

YT_HOSTS = {'youtube.com', 'www.youtube.com', 'm.youtube.com',
            'music.youtube.com', 'youtu.be', 'www.youtu.be'}

# 주소에서 영상 id 를 뽑는 꼴 — 짧은 주소·watch·shorts·embed·live 를 모두 받는다
_YT_PATTERNS = [
    re.compile(r'youtu\.be/([\w-]{11})'),
    re.compile(r'[?&]v=([\w-]{11})'),
    re.compile(r'/(?:embed|shorts|live|v)/([\w-]{11})'),
]


def youtube_id(url):
    """유튜브 주소에서 영상 id(11자). 유튜브가 아니면 ''."""
    try:
        host = urllib.parse.urlparse(url).netloc.lower()
    except ValueError:
        return ''
    if host not in YT_HOSTS:
        return ''
    for rx in _YT_PATTERNS:
        m = rx.search(url)
        if m:
            return m.group(1)
    return ''


def start_seconds(url):
    """`t=90` · `t=1m30s` · `start=90` 를 초로 바꾼다. 없으면 0."""
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    raw = (q.get('t') or q.get('start') or [''])[0]
    if not raw:
        return 0
    if raw.isdigit():
        return int(raw)
    m = re.fullmatch(r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?', raw)
    if not m or not any(m.groups()):
        return 0
    h, mi, s = (int(x or 0) for x in m.groups())
    return h * 3600 + mi * 60 + s


def _public_host(url):
    """사설·루프백·링크로컬 대역으로 가는 주소를 막는다(SSRF)."""
    host = urllib.parse.urlparse(url).hostname
    if not host:
        return False
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return False
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            return False
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast):
            return False
    return True


def _get(url, limit=200_000):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read(limit)


def fetch_youtube(url):
    """oEmbed 로 제목·채널·썸네일을 가져온다. 키가 필요 없다.

    되돌리는 것은 dict, 실패하면 `{'error': ...}`. 404 는 비공개이거나 지워진
    영상이라는 뜻이므로 그대로 알려 준다(`is_dead` 로 세운다).
    """
    vid = youtube_id(url)
    if not vid:
        return {'error': '유튜브 주소가 아니다'}
    api = ('https://www.youtube.com/oembed?format=json&url='
           + urllib.parse.quote(f'https://www.youtube.com/watch?v={vid}', safe=''))
    try:
        data = json.loads(_get(api))
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 404):
            return {'error': '비공개이거나 삭제된 영상', 'dead': True, 'video_id': vid}
        return {'error': f'가져오기 실패 ({e.code})', 'video_id': vid}
    except Exception as e:                                   # noqa: BLE001
        return {'error': f'가져오기 실패 ({e})', 'video_id': vid}
    return {
        'kind': 'youtube',
        'video_id': vid,
        'title': (data.get('title') or '')[:200],
        'author': (data.get('author_name') or '')[:100],
        'start_sec': start_seconds(url),
    }


_TITLE_RX = re.compile(rb'<title[^>]*>(.*?)</title>', re.S | re.I)
_META_RX = re.compile(rb'charset=["\']?([\w-]+)', re.I)


def fetch_page(url):
    """블로그·사이트의 <title> 만 가져온다. 본문은 건드리지 않는다."""
    if not url.lower().startswith(('http://', 'https://')):
        return {'error': 'http(s) 주소가 아니다'}
    if not _public_host(url):
        return {'error': '바깥 주소가 아니다'}
    try:
        raw = _get(url)
    except Exception as e:                                   # noqa: BLE001
        return {'error': f'가져오기 실패 ({e})'}
    m = _TITLE_RX.search(raw)
    if not m:
        return {'kind': 'blog', 'title': '', 'author': ''}
    enc = 'utf-8'
    cm = _META_RX.search(raw[:2000])
    if cm:
        enc = cm.group(1).decode('ascii', 'ignore') or 'utf-8'
    try:
        title = m.group(1).decode(enc, 'replace')
    except LookupError:
        title = m.group(1).decode('utf-8', 'replace')
    title = re.sub(r'\s+', ' ', title).strip()
    host = urllib.parse.urlparse(url).netloc.replace('www.', '')
    return {'kind': 'blog', 'title': title[:200], 'author': host[:100]}


def fetch(url):
    """주소를 보고 알맞은 방법으로 메타를 가져온다."""
    url = (url or '').strip()
    if not url:
        return {'error': '주소가 비었다'}
    return fetch_youtube(url) if youtube_id(url) else fetch_page(url)
