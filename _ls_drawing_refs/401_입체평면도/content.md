'My' 탭의 색 배치도와 '성운' 탭의 **기본설계도 · 배식설계도**를 GPT 이미지 모델
(gpt-image-2.5-sunburst)에 주고 만든 **입체평면도**입니다(10회차).

'조감도' 탭과 달리 **원근이 없는 평행투영(축측투영)** 입니다. 멀리 있는 것도 가까이 있는 것과
같은 크기로 그려지므로 **평면도와 그대로 견주어 볼 수 있습니다** — 주택 여덟 채가 모두 같은
크기이고, 동측 6m 도로의 띠 폭이 위에서 아래까지 한결같습니다. 시점은 도면과 같은 방향에서
약 45° 올려본 것이라(깊이가 0.71 로 줄어 있습니다) 시설마다 그림자와 앞면이 보입니다.
도면 위쪽이 실개천, 왼쪽이 기존수림, 오른쪽과 아래가 6m 도로와 주택가입니다
(문제지 방위표로는 도면 **왼쪽이 북쪽**입니다).

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
   잔디를 덮고 있었습니다. 수림 경계를 왼쪽으로 당기고 저수지를 서쪽으로 되돌렸습니다(7회차).
   여기서 시설·수목·투영은 모두 도면과 맞았고, 서쪽 절반이 6~7%쯤 동쪽으로 밀린 것만 남았습니다
8. 남은 비율을 **"수림 동단은 부지 폭의 12% 지점 · 남측 도로는 50%에서 시작 · 저수지는 14~44%"**
   라는 백분율로 못박아 새로 렌더했습니다(8회차). **하나도 반영되지 않았습니다** — 앞 회차 그림을
   참고로 주면 모델이 그 구도를 그대로 베낍니다
9. 그래서 앞 회차 그림을 **"시점·질감·물체 모양만 보고 위치·크기는 절대 가져오지 마라"** 로 돌리고
   좌표를 더 촘촘히 적어 보았습니다(9회차). 이것도 구도가 그대로였습니다.
   **모델은 백분율·좌표로 배치를 옮기지 못합니다**
10. 마지막으로 **비율이 아니라 "무엇을 지워라"** 로 바꿔 적었습니다(10회차) — "관찰로 서쪽과
    저수지 서쪽의 열린 땅에서 나무를 모두 지우고 빈 잔디로 둘 것, 짙은 수림은 왼쪽 가장자리의
    좁은 띠뿐, 빽빽한 숲은 관찰로 아래쪽에만". **이번에는 한 번에 고쳐졌습니다.**
    서쪽이 도면처럼 열린 잔디가 되고 저수지와 관찰로가 그만큼 서쪽으로 물러났습니다

> 회차마다 색 배치도와 배식설계도를 첫 두 참고 그림으로 다시 주고, 앞 회차 그림을 셋째로 줍니다.
> 마스크 부분 수정이나 그림을 손으로 자르고 돌리는 일은 하지 않습니다.

**투영은 재서 확인할 수 있는 조건으로, 배치는 "무엇을 지워라"로 적어야 합니다.**
"원근 없이"라고만 하면 1회차처럼 은근한 투시가 남습니다 — "부지가 사다리꼴이 아니라 평행사변형이다 ·
도로 띠 폭이 위아래로 같다 · 주택이 모두 같은 크기다"처럼 바꿔 적어야 고쳐집니다. 시점 각도도
말로는 안 움직이고 **"깊이를 몇 %로 줄여라"** 라야 움직입니다. 그런데 **배치는 백분율이 통하지
않습니다**(8·9회차 연속 실패) — 모델은 "부지 폭의 12% 지점"을 재지 못합니다. 대신
**"이 땅의 나무를 지우고 빈 잔디로 둬라"** 처럼 무엇을 그리고 무엇을 지울지로 적으면 한 번에 됩니다.

## 도면과 대조 (10회차)

| 항목 | 도면 | 그림 |
| --- | --- | --- |
| 투영 | 평행투영(축측투영) | ✓ 도로 띠 폭 70~74px 로 일정 · 모형 왼쪽 변이 730px 내려가는 동안 18px(1.4°) · 주택 8채가 같은 크기 |
| 부지 | 90m × 60m 직사각형 | ✓ 폭 1,316px(14.6px/m) · 깊이는 0.71 로 줄어 있음(약 45° 올려봄) |
| 주변 | 위 실개천, 왼쪽·아래왼쪽 야산과 기존수림, 오른쪽 6m 도로와 주택가, 아래 오른쪽 절반에 6m 도로 | ✓ (7·10회차에 수림을 왼쪽 좁은 띠로 당김) |
| 저수지구 | 왼쪽 위, 실개천에 붙은 자연형 연못 · 버드나무 5 · 부들·갈대 | ✓ (10회차에 서쪽으로 물러남) |
| 조류관찰소 | 저수지 남동 물가, 관찰로에 붙어 1개소 | ✓ 1개 — 지붕 아래 앞벽과 기둥이 보임 |
| 습지지구 | 가운데, 자연형 호안의 작은 연못 · 갈대·부들·돌 | ✓ |
| 관찰로 | 목재데크, 습지를 다각형으로 한 바퀴 돌아 모임광장에서 닫힘 | ✓ 닫힌 고리 · 데크 옆면·난간·하부 기둥·그림자까지 |
| 관찰데크 | 5개소, 안내판 5개 | ✓ 5개 · 각각 빈 안내판 1개 |
| 휴게공간 | 8m × 8m, 파고라 4×4 1 · 평의자 · 휴지통 1 | ✓ 파고라 1(기둥 4개와 살대 그림자) · 평의자 2 · 휴지통 1 · 그늘목 |
| 모임광장 | 습지 동쪽, 서쪽 안내판 3 · 수목보호대 1 | ✓ (안내판은 2회차, 보호대는 6회차에 고침) |
| 진입광장 | 2개소(북동 모서리 · 남측), 종합안내판 1 · 수목보호대 2씩, 도로로 바로 열림 | ✓ 보호대 합계 5개(모임광장 1 + 진입광장 2+2) |
| 남북 동선 | 두 진입광장을 잇는 소형고압블록 포장 | ✓ 동측 도로와 평행 |
| 배식 | 동선 서쪽 메타세쿼이아 열식 · 동쪽 마운딩에 소나무 7 + 철쭉 · 도로변 은행나무 열식 · 산림지구 다층림 · 저수지·관찰로 서쪽은 열린 잔디 | ✓ (4·5·6·10회차에 고침 — 한 줄로, 포장 아닌 잔디 위에, 서쪽은 비움) |
| 글자 | 없음 | ✓ |

남은 차이는 **저수지가 도면보다 조금 동쪽·넓다**는 것(도면 부지 폭의 14~44%, 그림 약 19~50%)과
**남측 도로가 55% 지점에서 시작**한다는 것(도면 50%)입니다.

비용은 10장 약 $0.41 입니다.

## 프롬프트 — 마지막 회차(10회차, 참고: 색 배치도 + 배식설계도 + 7회차 그림)

앞 회차 그림을 함께 주고 "무엇을 지울지"만 적은 것입니다. 1~9회차 프롬프트는 뺐습니다.

    The FIRST attached image is the authoritative colour-coded site plan (top-down) of a small Korean ecological park. The SECOND attached image is the hand-drawn planting plan. The THIRD attached image is an axonometric model of the same park: copy its CAMERA, its PARALLEL PROJECTION, its MODEL STYLE, its LIGHTING and the three-dimensional shape of every object.

    Render this fresh and sharp. Keep the third image's composition and every one of its objects, and make ONE change.

    THE ONE CHANGE — CLEAR THE TREES OUT OF THE WESTERN LAWN.
    Look at the left half of the third image: a dense mass of trees runs from the left edge across almost a third of the park and presses right up against the west side of the timber boardwalk ring and against the west shore of the reservoir.

    In the first image that ground is NOT wooded. It is plain light-green mown grass. The dark woodland there is only a NARROW STRIP down the very left edge of the park — about as wide as the reservoir is tall, no wider.

    So: DELETE the trees from the open ground between that narrow left-edge strip and the boardwalk ring, and between the strip and the reservoir. Leave plain, empty, light-green mown grass there — no canopy, no shrub masses, no flowering bushes. At most three or four isolated single specimen trees standing well apart on the open lawn, as the first image shows. The result must read as a broad open meadow wrapping round the west of the reservoir and the west and south-west of the boardwalk ring.

    Then let the reservoir and the boardwalk ring sit further WEST, in the room the trees have given up, so the reservoir's west shore comes close to the narrow left-edge strip. Everything east of the boardwalk ring — the gathering plaza, the straight path, the mound, the entrance plazas, the roads, the houses — stays exactly where it is.

    Two related corrections:
    - The DENSE WOODLAND belongs in the LOWER LEFT and the LOWER MIDDLE, below the boardwalk ring, where it is the newly planted multi-layered woodland merging into the existing forest. It may fill the bottom-left third. It must NOT climb up the left side past the reservoir.
    - The 6 m road along the bottom edge begins at the MIDDLE of the bottom edge and runs to the bottom-right corner, covering the whole right half. In the third image it begins too far right.

    CAMERA AND PROJECTION — copy from the third image exactly:
    - PARALLEL (axonometric) projection. NO perspective, NO vanishing point, NO convergence anywhere.
    - The ground slab is a rectangle seen from 45 degrees above, its DEPTH foreshortened to 0.71 of true, exactly as in the third image. Nothing rotated: far and near edges exactly HORIZONTAL and parallel, left and right edges exactly VERTICAL and parallel, and the slab NOT wider at its near edge than at its far edge.
    - Every line running far-to-near runs in one single direction and never converges with the others; every line running left-to-right runs in one single other direction.
    - An object near the bottom of the picture is exactly the same size as the identical object near the top: all houses the same size, all ginkgos in a row the same size, all paving blocks the same size. All vertical edges exactly vertical and parallel.
    - Same orientation and framing: stream and reservoir at the TOP, narrow woodland strip on the LEFT, road and houses on the RIGHT, second road and houses along the BOTTOM RIGHT.
    - Same clean matte low-poly model look, same soft even light, same short shadows toward the bottom, the near-facing side of every object visible and shaded, an earth-coloured side face along the slab's near and left edges. Crisp and sharply detailed.

    EVERYTHING ELSE IS EXACTLY AS IN THE THIRD IMAGE:
    - The stream crossing the whole top with a wooded hillside beyond it.
    - The reservoir with 5 willows, reed and cattail beds and shoreline stones; the wetland pond inside the ring, likewise reeded and stoned.
    - ONE closed ANGULAR ring of raised timber boardwalk round the wetland, with deck edge, rails and low posts; both right-hand ends meeting the gathering plaza; its upper-left run along the reservoir's lower shore.
    - EXACTLY 5 square timber viewing platforms bumping out from the boardwalk, each with one blank board: on the upper run at the reservoir shore, on the upper-right run near the hut, on the left run, on the lower-left diagonal run, on the lower run near the rest area.
    - EXACTLY 1 timber bird-watching hut, hipped roof over a visible front wall, on the reservoir's lower-right shore.
    - The rest area: EXACTLY 1 pergola on four visible posts under a slatted roof, 2 flat benches on its left, 1 litter bin, shaded by a group of broad deciduous trees.
    - The gathering plaza: EXACTLY 3 blank signboards in a row along its left edge, EXACTLY 1 zelkova in a square grate.
    - The top-right entrance plaza: EXACTLY 2 zelkovas in grates, 1 blank signboard on its left edge, opening onto the right-hand road.
    - The bottom entrance plaza: EXACTLY 2 zelkovas in grates side by side, 1 blank signboard on its left edge, opening onto the bottom road. FIVE tree grates in all.
    - ONE single evenly spaced row of about 12 conical dawn redwoods on the grass immediately LEFT of the straight block-paved path — one row only, never two, never on the paving.
    - The long mound east of the path: EXACTLY 7 spreading pines with azalea masses, near slope lit, far slope shaded, in open mown lawn.
    - ONE single row of yellow-green ginkgos inside the right-hand road, continuing inside the bottom road.
    - Grey-roofed houses of identical size beyond both roads, each showing a lit front wall.

    STRICT RULES: no new buildings, plazas, paths, bridges, fences, walls or car parks; every board and sign is blank; NO text, letters, numbers, labels, legends, arrows, north arrow, scale bar, grid lines, dimension lines or watermark anywhere; no sky, no horizon, plain neutral background.
