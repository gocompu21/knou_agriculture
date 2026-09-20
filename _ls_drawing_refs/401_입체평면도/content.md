'My' 탭의 색 배치도와 '성운' 탭의 **기본설계도 · 배식설계도**를 GPT 이미지 모델
(gpt-image-2.5-sunburst)에 주고 만든 **입체평면도**입니다(22회차).

'조감도' 탭과 달리 **원근이 없는 평행투영(축측투영)** 입니다. 멀리 있는 것도 가까이 있는 것과
같은 크기로 그려지므로 **평면도와 그대로 견주어 볼 수 있습니다** — 주택 여덟 채가 모두 같은
크기이고, 동측 6m 도로의 띠 폭이 위에서 아래까지 한결같습니다. 시점은 도면과 같은 방향에서
약 45° 올려본 것이라(깊이가 0.71 로 줄어 있습니다) 시설마다 그림자와 앞면이 보입니다.
도면 위쪽이 실개천, 왼쪽이 기존수림, 오른쪽과 아래가 6m 도로와 주택가입니다
(문제지 방위표로는 도면 **왼쪽이 북쪽**입니다).

질감은 **실사 렌더**입니다 — 잎이 하나하나 보이는 수관, 결이 보이는 잔디, 반사가 비치는 수면,
나뭇결이 살아 있는 데크와 파고라, 실제 콘크리트 블록 포장과 아스팔트. 10회차까지는 점토 모형
같은 그림이었는데 11~13회차에 질감만 바꿨고, 14~16회차에 마운딩 가장자리 식재를 더했습니다(아래 참조).

## 만든 방법

1. 색 배치도와 기본설계도를 참고 그림으로 주고 도면을 글로 풀어 쓴 프롬프트로 그렸습니다(1회차).
   배치·시설 수는 거의 맞았으나 **원근 투시**로 그려져 부지가 사다리꼴이 되고 아래로 갈수록
   넓어졌습니다. 도로 띠 폭을 재 보니 높이에 따라 77~413px 로 들쭉날쭉했습니다.
   모임광장 서쪽 안내판도 2개뿐이었습니다
2. **도면 + 1회차 그림**을 주고 "배치·색·틀은 그대로 두고 투영만 평행으로"라고 했습니다(2회차).
   부지가 평행사변형이 되고 도로 띠 폭이 어느 높이에서나 156px 로 일정해졌습니다. 안내판도 3개로
3. 그래도 아래쪽이 8% 벌어지는 부채꼴이 남아 "네 변이 모두 곧고, 아래가 위보다 넓지 않게"를
   못박았습니다(3회차). 완전한 평행투영이 됐지만 이번에는 **거의 바로 위에서 본 모습**이 되어
   입체감이 사라졌습니다
4. **배식설계도를 참고 그림에 더해** 수목을 도면대로 고쳤습니다(4회차) — 마운딩 소나무 7주,
   메타세쿼이아 열식, 도로변 은행나무 열식, 휴게공간 그늘목, 저수지 버드나무, 다층구조 신규림.
   시점은 그대로였고 메타세쿼이아가 두 줄이 됐습니다
5. "깊이를 45%로 줄여라"라고 수치를 박아 시점을 낮추고 메타세쿼이아를 한 줄로 되돌렸습니다
   (5회차). 대신 모임광장의 수목보호대 한 개가 사라졌습니다
6. 수목보호대를 되살리고, 포장 위에 서 있던 메타세쿼이아를 옆 잔디로 옮기고, 시설마다
   앞면과 그림자가 보이도록 했습니다(6회차)
7. 도면과 대조하니 **기존수림이 오른쪽으로 너무 자라** 저수지를 동쪽으로 밀어내고 관찰로 서쪽
   잔디를 덮고 있었습니다. 수림 경계를 왼쪽으로 당기고 저수지를 서쪽으로 되돌렸습니다(7회차)
8. 남은 비율을 **"수림 동단은 부지 폭의 12% 지점 · 남측 도로는 50%에서 시작 · 저수지는 14~44%"**
   라는 백분율로 못박아 새로 렌더했습니다(8회차). **하나도 반영되지 않았습니다** — 앞 회차 그림을
   참고로 주면 모델이 그 구도를 그대로 베낍니다
9. 앞 회차 그림을 **"시점·질감·물체 모양만 보고 위치·크기는 절대 가져오지 마라"** 로 돌리고
   좌표를 더 촘촘히 적어 보았습니다(9회차). 이것도 구도가 그대로였습니다.
   **모델은 백분율·좌표로 배치를 옮기지 못합니다**
10. **비율이 아니라 "무엇을 지워라"** 로 바꿔 적었습니다(10회차) — "관찰로 서쪽과 저수지 서쪽의
    열린 땅에서 나무를 모두 지우고 빈 잔디로 둘 것, 짙은 수림은 왼쪽 가장자리의 좁은 띠뿐,
    빽빽한 숲은 관찰로 아래쪽에만". **한 번에 고쳐졌습니다**
11. 여기까지는 점토·플라스틱 모형 같은 그림이었습니다. **배치·시점·평행투영은 그대로 두고 질감만**
    실사로 바꿨습니다(11회차) — 잎이 보이는 수관, 결이 보이는 잔디, 반사가 있는 수면, 나뭇결이
    보이는 목재, 실제 콘크리트 블록·아스팔트. 평행투영 문장을 같은 프롬프트에 그대로 남겨 둔 덕에
    **원근으로 되돌아가지 않았습니다**. 다만 모임광장 안내판이 3개에서 2개로 줄었습니다
12. 안내판과 마운딩을 함께 고치라고 했더니(12회차) 마운딩만 잔디 언덕으로 돌아오고 안내판은
    그대로 2개였으며, 선명도까지 떨어졌습니다(1790 → 1161). 채택하지 않았습니다
13. 11회차 그림으로 돌아가 **"그 줄을 세어 하나, 둘, 셋이 되도록 세 번째 안내판을 그려라"** 라고
    적으니 3개가 됐고 마운딩도 잔디 언덕이 됐습니다(13회차)
14. 배식설계도와 대조하니 **마운딩 화단의 가장자리 식재가 빠져** 있었습니다(사용자 지적). 도면에는
    화단 서쪽 변과 남쪽 변을 따라 구름 모양 윤곽의 **끊기지 않는 관목 띠**가 있는데 그림은 왼쪽이
    맨 잔디였습니다. **"왼쪽 가장자리를 따라 낮은 꽃관목을 한 줄로 빈틈없이 심고, 아래쪽 끝에서
    오른쪽으로 꺾어 아래 변도 따라가라 · 가운데 소나무 일곱 주와 철쭉은 그대로 둬라"** 로 적어
    띠가 생겼습니다(14회차). 다만 그림 전체 선명도가 20% 떨어졌습니다
15. 같은 지시에 "새로 렌더하고 어느 부분도 13회차보다 흐려지면 안 된다"를 더해 다시 그렸으나
    선명도는 거의 그대로였습니다(15회차) — **덧그릴 때마다 조금씩 물러지는 것은 프롬프트로는
    막지 못합니다**
16. 렌더 품질을 `high` 에서 **`xhigh`** 로 올려 다시 그렸습니다(16회차). 띠는 도면처럼 왼쪽 변
    전체를 지나 아래 변까지 이어졌고, 선명도가 14·15회차보다 올라가 13회차와 1:1 확대에서
    구분되지 않는 수준이 됐습니다. 이것을 채택했습니다
17. 성운 시설물 수량표를 다시 보니 **모임광장 서쪽 셋은 안내판이 아니라 평의자**였습니다 —
    평의자 8 · 안내판 6 · 종합안내판 1 인데 안내판 6은 관찰데크 5 + 조류관찰소 1 로 이미 다 차고,
    평의자 8 − 휴게공간 5 = 3 이 모임광장 몫입니다. 이때 **16회차 위에 또 얹지 않고 13회차로
    돌아가** '가장자리 띠'와 '평의자 3'을 **한 프롬프트에 넣어 한 번에** 그렸습니다(17회차).
    자리는 **"보도가 데크와 만나는 왼쪽 변, 수목보호대에 심긴 나무 바로 왼쪽"** 으로 짚고
    **"관찰데크 5 + 조류관찰소 1 안내판은 지우지 마라"** 를 따로 못박았습니다.
    선명도가 16회차보다 오히려 **2% 올라갔습니다**(1015 → 1033)
18. 안내판의 **흰 판이 멀리서 흰 점으로 도드라진다**는 지적을 받아, 다시 **13회차로 돌아가**
    '가장자리 띠 · 평의자 3 · 판면을 짙은 나뭇결 목재로' 셋을 한 프롬프트에 넣어 그렸습니다(18회차).
    판면이 어두워졌으나 이번에는 **주변과 안 어울린다**는 지적이 나왔습니다
19. 다시 13회차로 돌아가 네 가지(가장자리 띠 · 평의자 3 · **판면을 아주 연한 미색으로** ·
    **진입광장 안내판을 광장 변과 나란히**)를 한 번에 그렸습니다(19회차). 선명도가 **1117** 로
    18회차(1038)보다 올랐고, 평행투영도 그대로입니다 — 동측 도로 띠 왼끝 1353·1356·1361px
20·21. 다시 13회차로 돌아가 두 가지를 더했습니다 — **진입광장 안내판을 제자리에서 90° 돌려**
    판의 긴 변이 포장과 관목이 만나는 경계선과 나란해지게 하고(그 전에는 직각), 빈 미색 판이
    눈을 끌지 않도록 **읽히지 않을 만큼 흐린 회색 무늬**를 넣었습니다. 안내판은 **진입광장마다
    하나씩**입니다. 선명도 1052, 평행투영 그대로
22. 90° 를 돌리고 나니 판이 **누워** 평의자처럼 보인다는 지적 — 방향은 그대로 두고 **다리 위에 곧게 선 판**으로 모양만 고쳤습니다. 선명도 1028, 평행투영 그대로

> 회차마다 색 배치도와 배식설계도를 첫 두 참고 그림으로 다시 주고, 앞 회차 그림을 셋째로 줍니다.
> 마스크 부분 수정이나 그림을 손으로 자르고 돌리는 일은 하지 않습니다.

**투영은 재서 확인할 수 있는 조건으로, 배치와 개수는 "무엇을 지우고 무엇을 그려라"로 적어야 합니다.**
"원근 없이"라고만 하면 1회차처럼 은근한 투시가 남습니다 — "부지가 사다리꼴이 아니라 평행사변형이다 ·
도로 띠 폭이 위아래로 같다 · 주택이 모두 같은 크기다"처럼 바꿔 적어야 고쳐집니다. 시점 각도도
말로는 안 움직이고 **"깊이를 몇 %로 줄여라"** 라야 움직입니다. 그런데 **배치는 백분율이 통하지
않습니다**(8·9회차 연속 실패). 개수도 "3개여야 한다"로는 안 되고(11·12회차) **"세어서 하나, 둘,
셋이 되도록 세 번째를 그려라"** 라야 됐습니다(13회차). 빠진 식재도 마찬가지로 "가장자리를
따라 한 줄로 빈틈없이 심어라"로 적어 한 번에 됐습니다(14회차).

**덧그리기를 거듭하면 그림이 조금씩 물러집니다.** 14회차에서 선명도가 20% 떨어졌고 프롬프트로는
막지 못했습니다(15회차). 렌더 품질을 `xhigh` 로 올리니 회복됐습니다(16회차). **고칠 것이 또 생기면
마지막 그림 위에 얹지 말고, 덧그림이 적은 앞 회차로 돌아가 고칠 것을 모두 한 프롬프트에 넣어
다시 그리는 편이 낫습니다** — 17회차가 그렇게 해서 오히려 선명해졌습니다.

**실사를 주문하면 모델이 원근으로 되돌아가기 쉽습니다.** 11회차에 질감만 바꾸면서도 평행투영
문장을 통째로 남겨 두었고, 회차마다 화소로 재서 확인했습니다 — 동측 도로 띠 왼쪽 끝이
10회차 1351·1349·1361px, 16회차 1353·1356·1361px 로 같고, 모형 왼쪽 변 기울기도
10회차 −18px, 16회차 −16px(730px 기준)로 같습니다.

## 도면과 대조 (22회차)

| 항목 | 도면 | 그림 |
| --- | --- | --- |
| 투영 | 평행투영(축측투영) | ✓ 동측 도로 띠 왼쪽 끝이 1353·1356·1361px(높이별) · 모형 왼쪽 변이 730px 내려가는 동안 16px · 주택 8채가 같은 크기 |
| 부지 | 90m × 60m 직사각형 | ✓ 폭 1,316px · 깊이는 0.71 로 줄어 있음(약 45° 올려봄) |
| 질감 | — | ✓ 실사 렌더 — 잎이 보이는 수관 · 결이 있는 잔디 · 반사가 비치는 수면 · 나뭇결이 보이는 데크와 파고라 · 콘크리트 블록 포장과 아스팔트 |
| 주변 | 위 실개천, 왼쪽·아래왼쪽 야산과 기존수림, 오른쪽 6m 도로와 주택가, 아래 오른쪽 절반에 6m 도로 | ✓ (7·10회차에 수림을 왼쪽 좁은 띠로 당김) |
| 저수지구 | 왼쪽 위, 실개천에 붙은 자연형 연못 · 버드나무 5 · 부들·갈대 | ✓ |
| 조류관찰소 | 저수지 남동 물가, 관찰로에 붙어 1개소 | ✓ 1개 — 지붕 아래 앞벽과 창이 보임 |
| 습지지구 | 가운데, 자연형 호안의 작은 연못 · 갈대·부들·돌 | ✓ |
| 관찰로 | 목재데크, 습지를 다각형으로 한 바퀴 돌아 모임광장에서 닫힘 | ✓ 닫힌 고리 · 데크 널 이음매·난간·하부 기둥·그림자까지 |
| 관찰데크 | 5개소, 안내판 5개 | ✓ 5개 · 각각 빈 안내판 1개 |
| 휴게공간 | 8m × 8m, 파고라 4×4 1 · 평의자 · 휴지통 1 | ✓ 파고라 1(기둥 4개와 살대 그림자) · 평의자 2 · 휴지통 1 · 그늘목 |
| 모임광장 | 습지 동쪽, 서쪽 **평의자 3** · 수목보호대 1 | ✓ (17회차에 안내판 3개를 평의자 3개로 바꿈) |
| 진입광장 | 2개소(북동 모서리 · 남측), 종합안내판 1 · 수목보호대 2씩, 도로로 바로 열림 | ✓ 보호대 합계 5개(모임광장 1 + 진입광장 2+2) |
| 남북 동선 | 두 진입광장을 잇는 소형고압블록 포장 | ✓ 동측 도로와 평행 |
| 배식 | 동선 서쪽 메타세쿼이아 열식 · 동쪽 마운딩에 소나무 7 + 철쭉 · 도로변 은행나무 열식 · 산림지구 다층림 · 저수지·관찰로 서쪽은 열린 잔디 | ✓ 마운딩은 잔디 언덕에 소나무 7주(13회차), 서쪽 변과 남쪽 변을 따라 끊기지 않는 꽃관목 띠(16회차) |
| 안내판 판면 | — | ✓ 아주 연한 미색에 **읽히지 않는 흐린 무늬** — 옆 포장과 비슷한 밝기 |
| 안내판 방향·수 | — | ✓ 진입광장 안내판은 **포장·관목 경계선과 나란히**, 광장마다 **1개씩**. 관찰데크 5 · 조류관찰소 1 은 그대로 |
| 안내판 모양 | — | ✓ 안내판은 **다리 위에 곧게 선 판**입니다 — 가로로 누운 널빤지가 아니라서 모임광장·휴게공간의 갈색 평의자와 뚜렷이 구별됩니다. 미색 판면이 비스듬히 보이고 바닥에 선 판의 그림자가 집니다. |
| 글자 | 없음 | ✓ |

남은 차이는 둘입니다. ① **저수지가 도면보다 조금 동쪽·넓습니다**(도면 부지 폭의 14~44%, 그림 약 19~50%). ② **남측 도로가 55% 지점에서 시작**합니다(도면 50%).

비용은 22장 약 $1.14 입니다(16~22회차만 `xhigh` 품질이라 장당 $0.074).

## 프롬프트 — 마지막 회차(22회차, 참고: 색 배치도 + 배식설계도 + 13회차 그림)

13회차 그림을 함께 주고 고칠 넷만 적은 것입니다. 1~20회차 프롬프트는 뺐습니다.

    The FIRST attached image is the colour-coded site plan of a small Korean ecological park. The SECOND is its hand-drawn planting plan. The THIRD attached image is a PHOTOREALISTIC axonometric render of the same park. Its LAYOUT, its CAMERA, its PARALLEL PROJECTION, its MATERIALS, its TEXTURES, its LIGHTING and every one of its objects are CORRECT and must be reproduced exactly. It stays photorealistic.

    Four things are wrong. Fix exactly these four. Change nothing else at all.

    FIX 1 — THE MISSING SHRUB EDGING ON THE MOUND.
    Find the long grassy mound: the low turf hill in the open lawn east of the straight block-paved path, the one planted with seven pines and pink azaleas down its middle. Its LEFT side, where the turf meets the block paving of the path, is at present BARE GRASS, with only two or three loose clumps of shrubs at its top end and one near its bottom end.

    PLANT A CONTINUOUS BAND OF LOW FLOWERING SHRUBS ALONG THAT LEFT EDGE. It is one unbroken ribbon of dense, rounded, knee-high flowering shrubs — the same kind and the same colours as the clumps already there — about two or three shrubs deep, hugging the turf edge where it meets the paving. It STARTS at the very top end of the mound and runs all the way DOWN to the bottom end without a single gap, and at the bottom end it TURNS RIGHT and runs along the bottom edge of the mound's lawn as well, so the ribbon makes an L. Its outer line is soft and lobed like a natural shrub mass, not a clipped straight hedge. Existing loose clumps at the ends are absorbed into this continuous ribbon.

    WHAT DOES NOT CHANGE ON THE MOUND: the SEVEN pines down its middle stay exactly where they are, at the same size; the pink azalea masses between and around those pines stay exactly where they are; the mound stays a soft grassy hill whose turf runs on into the lawn, with its near slope lit and its far slope shaded. Do not add a clipped hedge border, a kerb, bare soil or a planting bed outline. Do not add shrubs anywhere else in the park.

    FIX 2 — THE THREE THINGS ON THE GATHERING PLAZA ARE BENCHES, NOT SIGNBOARDS.
    WHERE: the gathering plaza is the block-paved square just right of the timber boardwalk ring, the one with a single tree growing in a square metal grate set into its paving. On its LEFT edge, in the narrow strip of paving between the timber boardwalk deck and that tree, stands a vertical line of THREE tall timber frames holding WHITE PANELS, one above the other, facing out across the paving.

    DELETE all three frames and their white panels completely - frames, legs and panels. In exactly the same three spots put THREE BROWN TIMBER BENCHES, in the same vertical line and at the same even spacing. A bench is a long, low seat of brown timber slats lying flat on the paving, with no back and no upright panel of any kind - from this high viewpoint it reads as a narrow plank on the ground, never a standing board. All three are identical in length, width, timber and orientation.

    When you are done, that strip carries THREE IDENTICAL BROWN TIMBER BENCHES and nothing else. Count them: one bench, two benches, three benches. There is NO white panel, NO timber frame, NO standing board and NO sign of any kind left anywhere on this plaza. The tree in its square metal grate stays exactly where it is, immediately to their right.

    DO NOT TOUCH THE OTHER SIGNBOARDS. The small blank white boards on the five timber viewing platforms of the boardwalk, and the one at the bird-watching hut, MUST ALL STAY - six boards in all, each with a pale off-white panel, at the same places, the same sizes and the same square alignment. Do not delete them, do not move them and do not turn them into benches. The large blank boards on the two entrance plazas also stay. Only the three frames on the gathering plaza change.

    FIX 3 — THE BOARD PANELS ARE PALE OFF-WHITE WITH VERY FAINT, UNREADABLE MARKINGS.
    Every signboard in the picture - the 5 small boards on the 5 timber viewing platforms, the 1 board beside the bird-watching hut, and the large boards on BOTH entrance plazas - carries a panel inside its timber frame. That panel is a VERY PALE OFF-WHITE, a soft warm greyish cream, close in brightness to the block paving beside it so that it never reads as a bright white dot. On that panel, printed in VERY FAINT PALE GREY, is a simple notice: one small block of picture near the top and two or three short lines below it. Those markings must be SO FAINT AND SO BLURRED THAT THEY CANNOT BE READ - from a distance you can tell that something is printed on the board, but you cannot make out a single letter. Use no dark ink, no black strokes, no crisp lettering and no recognisable words in any language. The panel must NEVER be a smooth empty white surface, and it must NEVER carry legible text. Do not make the panel dark timber or any dark colour. Keep the timber frame and its legs exactly as they are, and do not remove or move any signboard.

    HOW MANY SIGNBOARDS THERE ARE. Each entrance plaza carries EXACTLY ONE signboard, never two - count them: one on the southern entrance plaza, one on the north-eastern entrance plaza. The boardwalk carries 5, one on each of the 5 viewing platforms, and there is 1 beside the bird-watching hut. SEVEN signboards in all in the whole park, no more and no fewer. The gathering plaza has NO signboard at all - it has three timber benches.

    FIX 4 — THE TWO ENTRANCE-PLAZA SIGNBOARDS ARE UPRIGHT BOARDS ON LEGS - THEY ARE NOT BENCHES.
    On each entrance plaza the large signboard stands right beside the line where the block paving meets the mass of shrubs at the edge of the plaza, and its LONG EDGE RUNS ALONG that line, parallel to it, with its back to the shrubs. That DIRECTION is correct and must stay exactly as it is.

    What is wrong is its SHAPE: the board has become a flat plank lying face-up on the ground, exactly like a bench. It must instead be a BOARD STANDING UPRIGHT ON TWO SLIM TIMBER LEGS. The panel is held up on edge, its bottom edge well clear of the ground, and from this high viewpoint you see its PALE OFF-WHITE FACE at a slant, tilted towards the plaza, with the LONG SHADOW of the standing panel thrown across the paving beside it.

    IT MUST NOT LOOK LIKE A BENCH. This same picture contains brown timber benches - three on the gathering plaza and five at the pergola rest area. A BENCH is LOW, with a flat seat lying horizontally, and you look down onto its seat. A SIGNBOARD is TALL, stands on edge on its legs, and has nothing to sit on. The two must be unmistakably different at a glance. Never draw a signboard as a flat horizontal plank of timber.

    Do not move either board from its spot, and do not change its size or its direction. Do this on BOTH entrance plazas, the southern one and the north-eastern one.

    DO NOT TOUCH THE BOARDS ON THE BOARDWALK. The 5 small boards on the 5 timber viewing platforms and the 1 board beside the bird-watching hut are ALREADY RIGHT - each stands upright and runs along its own deck rail. Leave their shape, direction, position and size exactly as they are.

    SHARPNESS — RENDER THIS FRESH AT FULL RESOLUTION AND FULL DETAIL.
    Do not retouch or resample the third image: draw the whole picture again from scratch. Every part of it must be at least as crisp and as finely detailed as the third image is — the individual leaves in every canopy, the blades and mowing stripes in the turf, the board joints and grain of the boardwalk, the joints of the block paving, the roof tiles of the houses, the pebbles at the water edge. Nothing may come out softer, blurrier, smoother or more washed out than in the third image.

    THE RENDER STYLE STAYS PHOTOREALISTIC, exactly as in the third image:
    - Real broadleaf and conifer canopies with individual leaves, real branch structure, varied natural greens, rough bark. Never smooth spheres, cones or blobs of flat colour.
    - Real turf with visible blade texture and mowing direction. Real water with reflections and ripples. Real weathered timber with visible grain and board joints on the boardwalk, rails, platforms, hut and pergola. Real concrete block paving, real granite, real asphalt with concrete kerbs, real cast-metal tree grates, real roof tiles and rendered walls on the houses, real soil in the slab's cut face.
    - One natural sun from the upper left, soft realistic shadows, natural colour balance. No sky, no horizon, plain neutral background. Crisp and sharply detailed, not soft or blurred.
    - FORBIDDEN: plastic, clay, toy, miniature-model, low-poly, isometric game art, cartoon, illustration, flat over-saturated colours, outlines. It must look photographed.

    THE PROJECTION MUST NOT CHANGE — it is an ORTHOGRAPHIC camera, not a lens:
    - PARALLEL (axonometric) projection. NO perspective, NO vanishing point, NO convergence anywhere.
    - The ground slab is a PARALLELOGRAM, never a trapezoid: far edge and near edge exactly the same length and exactly horizontal; left and right edges exactly the same length and exactly vertical. The model is NOT wider at the bottom of the picture than at the top.
    - The right-hand road is a band of CONSTANT width from the top of the picture to the bottom; its two kerb lines straight and parallel. The same for the bottom road.
    - Every house is exactly the SAME size, near the top of the picture or near the bottom. The same for every ginkgo in its row, every dawn redwood in its row, every paving block, every tree grate.
    - Every line running far-to-near in the plan — the right-hand road, the straight path, the dawn redwood row, the ginkgo row, the mound — runs in one single direction and never converges with the others. Every line running left-to-right — the stream, the bottom road, the plaza kerbs — runs in one single other direction.
    - All vertical edges exactly vertical in the picture and exactly parallel to one another.
    - The camera stays 45 degrees above the ground, the slab's DEPTH foreshortened to 0.71 of true, exactly as in the third image. Same framing and orientation: stream and reservoir at the TOP, narrow woodland strip and forest on the LEFT and lower left, road and houses on the RIGHT, second road and houses along the BOTTOM RIGHT. Do not rotate, flip, zoom or crop.

    EVERYTHING ELSE IS EXACTLY AS IN THE THIRD IMAGE: the stream across the top with wooded hillside beyond; the reservoir with its willows, reed beds and shoreline stones; the wetland pond; ONE closed angular ring of raised timber boardwalk with EXACTLY 5 viewing platforms, each carrying one board with a pale off-white panel; EXACTLY 1 bird-watching hut on the reservoir's lower-right shore; the rest area with EXACTLY 1 pergola, 2 benches and 1 litter bin under shade trees; the gathering plaza with its EXACTLY 1 tree in a square grate; EXACTLY 2 trees in grates and 1 blank board on the top-right entrance plaza; EXACTLY 2 trees in grates and 1 blank board on the bottom entrance plaza — FIVE tree grates in all; ONE single row of about 12 dawn redwoods on the grass immediately LEFT of the straight path; ONE single row of ginkgos inside the right-hand road continuing inside the bottom road; open mown lawn west of the ring and west of the reservoir with only three or four isolated specimen trees; the dense multi-layered woodland only in the lower left and lower middle.

    STRICT RULES: no new buildings, plazas, paths, bridges, fences, walls, cars or people; NO text, letters, numbers, labels, legends, arrows, north arrow, scale bar, grid lines, dimension lines or watermark anywhere in the picture. The ONLY exception is the very faint, blurred, unreadable grey markings on the signboard panels described above - they must stay illegible.
