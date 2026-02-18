"""모든 과목을 일괄 스크래핑하여 엑셀로 저장하는 스크립트."""
import openpyxl
from scrape_exam import fetch_html, parse_page

BASE = 'https://allaclass.tistory.com'

ALL_SUBJECTS = [
    {
        'name': '시설원예학', 'exam_type': '기말시험',
        'pages': [
            (2019, 4, f'{BASE}/1239'), (2018, 4, f'{BASE}/1238'),
            (2017, 4, f'{BASE}/1237'), (2016, 4, f'{BASE}/1236'),
            (2015, 4, f'{BASE}/1235'), (2014, 4, f'{BASE}/1234'),
            (2013, 4, f'{BASE}/1233'),
        ],
    },
    {
        'name': '식용작물학2', 'exam_type': '기말시험',
        'pages': [
            (2019, 4, f'{BASE}/1257'), (2018, 4, f'{BASE}/1256'),
            (2017, 4, f'{BASE}/1255'), (2016, 4, f'{BASE}/1254'),
            (2015, 4, f'{BASE}/1253'), (2014, 4, f'{BASE}/1252'),
            (2013, 4, f'{BASE}/1251'),
        ],
    },
    {
        'name': '생활과건강', 'exam_type': '기말시험',
        'pages': [
            (2019, 4, f'{BASE}/1266'), (2018, 4, f'{BASE}/1265'),
            (2017, 4, f'{BASE}/1264'), (2016, 4, f'{BASE}/1263'),
            (2015, 4, f'{BASE}/1262'),
            (2019, 1, f'{BASE}/1261'), (2018, 1, f'{BASE}/1260'),
            (2017, 1, f'{BASE}/1259'), (2016, 1, f'{BASE}/1258'),
        ],
    },
    {
        'name': '원예작물학2', 'exam_type': '기말시험',
        'pages': [
            (2019, 4, f'{BASE}/1250'), (2018, 4, f'{BASE}/1249'),
            (2017, 4, f'{BASE}/1248'), (2016, 4, f'{BASE}/1247'),
            (2015, 4, f'{BASE}/1246'), (2014, 4, f'{BASE}/1245'),
            (2013, 4, f'{BASE}/1244'),
        ],
    },
    {
        'name': '동물사료학', 'exam_type': '기말시험',
        'pages': [
            (2019, 3, f'{BASE}/1232'), (2018, 3, f'{BASE}/1231'),
            (2017, 3, f'{BASE}/1230'), (2016, 3, f'{BASE}/1229'),
            (2015, 3, f'{BASE}/1228'), (2014, 3, f'{BASE}/1227'),
            (2013, 3, f'{BASE}/1226'),
        ],
    },
    {
        'name': '푸드마케팅', 'exam_type': '기말시험',
        'pages': [
            (2019, 4, f'{BASE}/1243'), (2019, 3, f'{BASE}/1242'),
            (2018, 4, f'{BASE}/1241'), (2017, 4, f'{BASE}/1240'),
        ],
    },
    {
        'name': '농업경영학', 'exam_type': '기말시험',
        'pages': [
            (2019, 4, f'{BASE}/975'), (2018, 4, f'{BASE}/974'),
            (2017, 4, f'{BASE}/973'), (2016, 4, f'{BASE}/972'),
            (2015, 4, f'{BASE}/971'), (2014, 4, f'{BASE}/970'),
            (2013, 4, f'{BASE}/969'),
        ],
    },
    {
        'name': '농축산식품이용학', 'exam_type': '기말시험',
        'pages': [
            (2019, 4, f'{BASE}/982'), (2018, 4, f'{BASE}/981'),
            (2017, 4, f'{BASE}/980'), (2016, 4, f'{BASE}/979'),
            (2015, 4, f'{BASE}/978'), (2014, 4, f'{BASE}/977'),
            (2013, 4, f'{BASE}/976'),
        ],
    },
    {
        'name': '식물분류학', 'exam_type': '기말시험',
        'pages': [
            (2019, 4, f'{BASE}/984'), (2018, 4, f'{BASE}/983'),
        ],
    },
    {
        'name': '농업유전학', 'exam_type': '기말시험',
        'pages': [
            (2019, 2, f'{BASE}/1189'), (2018, 2, f'{BASE}/1188'),
            (2017, 2, f'{BASE}/1187'), (2016, 2, f'{BASE}/1186'),
            (2015, 2, f'{BASE}/1185'), (2014, 2, f'{BASE}/1184'),
            (2013, 2, f'{BASE}/1183'),
        ],
    },
    {
        'name': '농업생물화학', 'exam_type': '기말시험',
        'pages': [
            (2019, 2, f'{BASE}/3082'), (2018, 2, f'{BASE}/3081'),
            (2017, 2, f'{BASE}/3080'), (2016, 2, f'{BASE}/3079'),
            (2015, 2, f'{BASE}/3078'), (2014, 2, f'{BASE}/3077'),
            (2013, 2, f'{BASE}/3076'),
        ],
    },
    {
        'name': '한국사의이해', 'exam_type': '기말시험',
        'pages': [
            (2019, 2, f'{BASE}/66'), (2018, 2, f'{BASE}/65'),
            (2017, 2, f'{BASE}/64'), (2016, 2, f'{BASE}/63'),
            (2015, 2, f'{BASE}/62'),
        ],
    },
    {
        'name': '세상읽기와논술', 'exam_type': '기말시험',
        'pages': [
            (2019, 2, f'{BASE}/222'), (2018, 2, f'{BASE}/221'),
            (2017, 3, f'{BASE}/220'), (2017, 2, f'{BASE}/219'),
        ],
    },
    {
        'name': '철학의이해', 'exam_type': '기말시험',
        'pages': [
            (2019, 2, f'{BASE}/508'), (2018, 2, f'{BASE}/507'),
            (2017, 2, f'{BASE}/506'), (2016, 2, f'{BASE}/505'),
        ],
    },
    {
        'name': '취미와예술', 'exam_type': '기말시험',
        'pages': [
            (2019, 2, f'{BASE}/515'), (2018, 2, f'{BASE}/514'),
            (2017, 2, f'{BASE}/513'), (2016, 2, f'{BASE}/512'),
            (2015, 2, f'{BASE}/511'), (2014, 2, f'{BASE}/510'),
            (2013, 2, f'{BASE}/509'),
        ],
    },
    {
        'name': '재배식물생리학', 'exam_type': '기말시험',
        'pages': [
            (2019, 2, f'{BASE}/942'), (2018, 2, f'{BASE}/941'),
            (2017, 2, f'{BASE}/940'), (2016, 2, f'{BASE}/939'),
            (2015, 2, f'{BASE}/938'), (2014, 2, f'{BASE}/937'),
            (2013, 2, f'{BASE}/936'),
        ],
    },
    {
        'name': '생활속의경제', 'exam_type': '기말시험',
        'pages': [
            (2019, 2, f'{BASE}/535'), (2018, 2, f'{BASE}/534'),
            (2017, 2, f'{BASE}/533'), (2016, 2, f'{BASE}/532'),
            (2015, 2, f'{BASE}/531'), (2014, 2, f'{BASE}/530'),
            (2013, 2, f'{BASE}/529'),
        ],
    },
    {
        'name': '원예학', 'exam_type': '기말시험',
        'pages': [
            (2019, 1, f'{BASE}/1175'), (2018, 1, f'{BASE}/1174'),
            (2017, 1, f'{BASE}/1173'), (2016, 1, f'{BASE}/1172'),
            (2015, 1, f'{BASE}/1171'), (2014, 1, f'{BASE}/1170'),
            (2013, 1, f'{BASE}/1169'),
        ],
    },
    {
        'name': '숲과삶', 'exam_type': '기말시험',
        'pages': [
            (2019, 1, f'{BASE}/1202'), (2018, 1, f'{BASE}/1201'),
            (2017, 1, f'{BASE}/1200'), (2016, 1, f'{BASE}/1199'),
            (2015, 1, f'{BASE}/1198'), (2014, 1, f'{BASE}/1197'),
            (2013, 1, f'{BASE}/1196'),
        ],
    },
    {
        'name': '컴퓨터의이해', 'exam_type': '기말시험',
        'pages': [
            (2019, 1, f'{BASE}/1333'), (2018, 1, f'{BASE}/1332'),
            (2017, 1, f'{BASE}/1331'), (2016, 1, f'{BASE}/1330'),
            (2015, 1, f'{BASE}/1329'),
        ],
    },
    {
        'name': '세계의역사', 'exam_type': '기말시험',
        'pages': [
            (2019, 1, f'{BASE}/39'), (2018, 1, f'{BASE}/38'),
            (2017, 1, f'{BASE}/37'), (2016, 1, f'{BASE}/36'),
        ],
    },
    {
        'name': '농학원론', 'exam_type': '기말시험',
        'pages': [
            (2019, 1, f'{BASE}/1182'), (2018, 1, f'{BASE}/1181'),
            (2017, 1, f'{BASE}/1180'), (2016, 1, f'{BASE}/1179'),
            (2015, 1, f'{BASE}/1178'), (2014, 1, f'{BASE}/1177'),
            (2013, 1, f'{BASE}/1176'),
        ],
    },
    {
        'name': '글쓰기', 'exam_type': '기말시험',
        'pages': [
            (2019, 3, f'{BASE}/141'), (2018, 3, f'{BASE}/140'),
            (2017, 3, f'{BASE}/139'),
            (2019, 1, f'{BASE}/138'), (2018, 1, f'{BASE}/137'),
            (2017, 1, f'{BASE}/136'), (2016, 1, f'{BASE}/135'),
            (2015, 1, f'{BASE}/134'), (2014, 1, f'{BASE}/133'),
            (2013, 1, f'{BASE}/132'),
        ],
    },
    {
        'name': '생물과학', 'exam_type': '기말시험',
        'pages': [
            (2019, 1, f'{BASE}/912'), (2018, 1, f'{BASE}/911'),
            (2017, 1, f'{BASE}/910'), (2016, 1, f'{BASE}/909'),
            (2015, 1, f'{BASE}/908'), (2014, 1, f'{BASE}/907'),
            (2013, 1, f'{BASE}/906'),
        ],
    },
    {
        'name': '인간과과학', 'exam_type': '기말시험',
        'pages': [
            (2019, 1, f'{BASE}/595'), (2018, 1, f'{BASE}/594'),
            (2017, 1, f'{BASE}/593'), (2016, 1, f'{BASE}/592'),
            (2015, 1, f'{BASE}/591'),
        ],
    },
    {
        'name': '재배학원론', 'exam_type': '기말시험',
        'pages': [
            (2019, 1, f'{BASE}/926'), (2018, 1, f'{BASE}/925'),
            (2017, 1, f'{BASE}/924'), (2016, 1, f'{BASE}/923'),
            (2015, 1, f'{BASE}/922'), (2014, 1, f'{BASE}/921'),
            (2013, 1, f'{BASE}/920'),
        ],
    },
    {
        'name': '축산학', 'exam_type': '기말시험',
        'pages': [
            (2019, 1, f'{BASE}/919'), (2018, 1, f'{BASE}/918'),
            (2017, 1, f'{BASE}/917'), (2016, 1, f'{BASE}/916'),
            (2015, 1, f'{BASE}/915'), (2014, 1, f'{BASE}/914'),
            (2013, 1, f'{BASE}/913'),
        ],
    },
    {
        'name': '심리학에게묻다', 'exam_type': '기말시험',
        'pages': [
            (2019, 1, f'{BASE}/478'), (2018, 1, f'{BASE}/477'),
            (2017, 1, f'{BASE}/476'), (2016, 1, f'{BASE}/475'),
            (2015, 1, f'{BASE}/474'), (2014, 1, f'{BASE}/473'),
            (2013, 1, f'{BASE}/472'),
        ],
    },
    # ── 추가 과목 ──
    {
        'name': '인간과교육', 'exam_type': '기말시험',
        'pages': [
            (2019, 3, f'{BASE}/492'), (2018, 3, f'{BASE}/491'),
            (2017, 3, f'{BASE}/490'), (2016, 3, f'{BASE}/489'),
            (2015, 3, f'{BASE}/488'), (2014, 3, f'{BASE}/487'),
            (2013, 3, f'{BASE}/486'),
            (2019, 1, f'{BASE}/485'), (2018, 1, f'{BASE}/484'),
            (2017, 1, f'{BASE}/483'), (2016, 1, f'{BASE}/482'),
            (2015, 1, f'{BASE}/481'), (2014, 1, f'{BASE}/480'),
            (2013, 1, f'{BASE}/479'),
        ],
    },
    {
        'name': '동서양고전의이해', 'exam_type': '기말시험',
        'pages': [
            (2019, 2, f'{BASE}/1195'), (2018, 2, f'{BASE}/1194'),
            (2017, 2, f'{BASE}/1192'), (2016, 2, f'{BASE}/1191'),
            (2015, 2, f'{BASE}/1190'),
        ],
    },
    {
        'name': '농축산환경학', 'exam_type': '기말시험',
        'pages': [
            (2019, 3, f'{BASE}/1204'), (2018, 3, f'{BASE}/1203'),
        ],
    },
    {
        'name': '생물통계학', 'exam_type': '기말시험',
        'pages': [
            (2019, 3, f'{BASE}/3107'), (2018, 3, f'{BASE}/3106'),
            (2017, 3, f'{BASE}/3105'), (2016, 3, f'{BASE}/3104'),
            (2015, 3, f'{BASE}/3103'), (2014, 3, f'{BASE}/3102'),
            (2013, 3, f'{BASE}/3101'),
        ],
    },
    {
        'name': '생활원예', 'exam_type': '기말시험',
        'pages': [
            (2019, 3, f'{BASE}/968'), (2018, 3, f'{BASE}/967'),
            (2017, 3, f'{BASE}/966'), (2016, 3, f'{BASE}/965'),
            (2015, 3, f'{BASE}/964'), (2014, 3, f'{BASE}/963'),
            (2013, 3, f'{BASE}/962'),
        ],
    },
    {
        'name': '식물의학', 'exam_type': '기말시험',
        'pages': [
            (2019, 3, f'{BASE}/1211'), (2018, 3, f'{BASE}/1210'),
            (2017, 3, f'{BASE}/1209'), (2016, 3, f'{BASE}/1208'),
            (2015, 3, f'{BASE}/1207'), (2014, 3, f'{BASE}/1206'),
            (2013, 3, f'{BASE}/1205'),
        ],
    },
    {
        'name': '식용작물학1', 'exam_type': '기말시험',
        'pages': [
            (2019, 3, f'{BASE}/956'), (2018, 3, f'{BASE}/955'),
            (2017, 3, f'{BASE}/954'), (2016, 3, f'{BASE}/953'),
            (2015, 3, f'{BASE}/952'), (2014, 3, f'{BASE}/951'),
            (2013, 3, f'{BASE}/950'),
        ],
    },
    {
        'name': '원예작물학1', 'exam_type': '기말시험',
        'pages': [
            (2019, 3, f'{BASE}/1745'), (2018, 3, f'{BASE}/1744'),
            (2017, 3, f'{BASE}/1743'), (2016, 3, f'{BASE}/1742'),
            (2015, 3, f'{BASE}/1741'), (2014, 3, f'{BASE}/1739'),
            (2013, 3, f'{BASE}/1738'),
        ],
    },
    {
        'name': '자원식물학', 'exam_type': '기말시험',
        'pages': [
            (2019, 3, f'{BASE}/1218'), (2018, 3, f'{BASE}/1217'),
            (2017, 3, f'{BASE}/1216'), (2016, 3, f'{BASE}/1215'),
            (2015, 3, f'{BASE}/1214'), (2014, 3, f'{BASE}/1213'),
            (2013, 3, f'{BASE}/1212'),
        ],
    },
    {
        'name': '재배식물육종학', 'exam_type': '기말시험',
        'pages': [
            (2019, 3, f'{BASE}/1225'), (2018, 3, f'{BASE}/1224'),
            (2017, 3, f'{BASE}/1223'), (2016, 3, f'{BASE}/1222'),
            (2015, 3, f'{BASE}/1221'), (2014, 3, f'{BASE}/1220'),
            (2013, 3, f'{BASE}/1219'),
        ],
    },
    {
        'name': '토양학', 'exam_type': '기말시험',
        'pages': [
            (2019, 3, f'{BASE}/961'), (2018, 3, f'{BASE}/960'),
            (2017, 3, f'{BASE}/959'), (2016, 3, f'{BASE}/958'),
            (2015, 3, f'{BASE}/957'),
        ],
    },
    {
        'name': '환경친화형농업', 'exam_type': '기말시험',
        'pages': [
            (2019, 3, f'{BASE}/949'), (2018, 3, f'{BASE}/948'),
            (2017, 3, f'{BASE}/947'), (2016, 3, f'{BASE}/946'),
            (2015, 3, f'{BASE}/945'), (2014, 3, f'{BASE}/944'),
            (2013, 3, f'{BASE}/943'),
        ],
    },
]


def scrape_subject(subj):
    name = subj['name']
    exam_type = subj['exam_type']

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = name
    ws.append(['학년도', '시험종류', '과목명', '학년', '문제번호', '문제', '1항', '2항', '3항', '4항', '답안'])

    total = 0
    for year, grade, url in subj['pages']:
        print(f'  {year} {grade}... ', end='', flush=True)
        try:
            html = fetch_html(url)
        except Exception as e:
            print(f'FAIL ({e})')
            continue

        questions = parse_page(html)
        if not questions:
            print('0 questions')
            continue

        for q in questions:
            ws.append([
                year, exam_type, name, grade,
                q['number'], q['text'],
                q['c1'], q['c2'], q['c3'], q['c4'],
                q['answer'] if q['answer'] else '',
            ])

        no_answer = sum(1 for q in questions if q['answer'] == '0')
        multi = sum(1 for q in questions if ',' in str(q['answer']))
        total += len(questions)
        msg = f'{len(questions)} questions'
        if multi:
            msg += f' ({multi} multi-answer)'
        if no_answer:
            msg += f' ({no_answer} no answer)'
        print(msg)

    output = f'data/{name}.xlsx'
    wb.save(output)
    print(f'  -> {total} questions saved to {output}')
    return total


def main():
    grand_total = 0
    for subj in ALL_SUBJECTS:
        print(f'\n[{subj["name"]}]')
        grand_total += scrape_subject(subj)
    print(f'\n=== Done: {grand_total} total questions across {len(ALL_SUBJECTS)} subjects ===')


if __name__ == '__main__':
    main()
