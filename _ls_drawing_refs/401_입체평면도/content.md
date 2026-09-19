'My' 탭의 색 배치도와 '성운' 탭의 **기본설계도 · 배식설계도**를 GPT 이미지 모델
(gpt-image-2.5-sunburst)에 주고 만든 **입체평면도**입니다(7회차).

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
7. 마지막으로 도면과 대조하니 **기존수림이 오른쪽으로 너무 자라** 저수지를 동쪽으로 밀어내고
   관찰로 서쪽 잔디를 덮고 있었습니다. 수림 경계를 왼쪽으로 당기고 저수지를 서쪽으로
   되돌렸습니다(7회차)

> 회차마다 색 배치도와 배식설계도를 첫 두 참고 그림으로 다시 주고, 앞 회차 그림을 셋째로 주어
> "나열한 것만 고치고 나머지는 그대로"라고 못박습니다. 마스크 부분 수정이나 그림을 손으로
> 자르고 돌리는 일은 하지 않습니다.

**평행투영은 말로만 시켜서는 안 됩니다.** "원근 없이"라고만 하면 1회차처럼 은근한 투시가
남습니다. "부지가 사다리꼴이 아니라 평행사변형이다 · 도로 띠 폭이 위아래로 같다 · 주택이 모두
같은 크기다"처럼 **재서 확인할 수 있는 조건**으로 바꿔 적어야 고쳐집니다. 반대로 시점 각도는
말로는 안 움직이고 **"깊이를 몇 %로 줄여라"** 라야 움직입니다.

## 도면과 대조 (7회차)

| 항목 | 도면 | 그림 |
| --- | --- | --- |
| 투영 | 평행투영(축측투영) | ✓ 도로 띠 폭 70~82px 로 일정 · 모형 왼쪽 변이 730px 내려가는 동안 17px(1.3°) · 주택 8채가 같은 크기 |
| 부지 | 90m × 60m 직사각형 | ✓ 폭 1,302px(14.5px/m) · 깊이는 0.71 로 줄어 있음(약 45° 올려봄) |
| 주변 | 위 실개천, 왼쪽·아래왼쪽 야산과 기존수림, 오른쪽 6m 도로와 주택가, 아래 오른쪽 절반에 6m 도로 | ✓ (7회차에 수림 경계를 당김) |
| 저수지구 | 왼쪽 위, 실개천에 붙은 자연형 연못 · 버드나무 · 부들·갈대 | ✓ (7회차에 서쪽으로 되돌림) |
| 조류관찰소 | 저수지 남동 물가, 관찰로에 붙어 1개소 | ✓ 1개 — 지붕 아래 앞벽과 기둥이 보임 |
| 습지지구 | 가운데, 자연형 호안의 작은 연못 · 갈대·부들·돌 | ✓ |
| 관찰로 | 목재데크, 습지를 다각형으로 한 바퀴 돌아 모임광장에서 닫힘 | ✓ 닫힌 고리 · 데크 옆면·난간·하부 기둥·그림자까지 |
| 관찰데크 | 5개소, 안내판 5개 | ✓ 5개 · 각각 빈 안내판 1개 |
| 휴게공간 | 8m × 8m, 파고라 4×4 1 · 평의자 · 휴지통 1 | ✓ 파고라 1(기둥 4개와 살대 그림자) · 평의자 2 · 휴지통 1 · 그늘목 |
| 모임광장 | 습지 동쪽, 서쪽 안내판 3 · 수목보호대 1 | ✓ (안내판은 2회차, 보호대는 6회차에 고침) |
| 진입광장 | 2개소(북동 모서리 · 남측), 종합안내판 1 · 수목보호대 2씩, 도로로 바로 열림 | ✓ 보호대 합계 5개(모임광장 1 + 진입광장 2+2) |
| 남북 동선 | 두 진입광장을 잇는 소형고압블록 포장 | ✓ 동측 도로와 평행 |
| 배식 | 동선 서쪽 메타세쿼이아 열식 · 동쪽 마운딩에 소나무 7 + 철쭉 · 도로변 은행나무 열식 · 산림지구 다층림 | ✓ (4·5·6회차에 고침 — 한 줄로, 포장 아닌 잔디 위에) |
| 글자 | 없음 | ✓ |

비용은 7장 약 $0.29 입니다.

## 프롬프트 — 마지막 회차(7회차, 참고: 색 배치도 + 배식설계도 + 6회차 그림)

앞 회차 그림을 함께 주고 "그것만 고치고 나머지는 그대로"라고 한 것입니다. 1~6회차 프롬프트는 뺐습니다.

    The FIRST attached image is the authoritative colour-coded site plan (top-down) of a small Korean ecological park, 90 m x 60 m. The SECOND attached image is the hand-drawn planting plan of the same site. The THIRD attached image is an axonometric model of that site. Its CAMERA ANGLE, PARALLEL PROJECTION, STYLE, LIGHTING, FRAMING and every built element are CORRECT — keep all of them and do not move the camera.

    One thing is wrong: in the third image the dark EXISTING FOREST on the left has grown too far to the right, and it has pushed the reservoir to the right with it. Compare with the first image.

    FIX — PULL THE LEFT-HAND FOREST BACK AND MOVE THE RESERVOIR BACK WEST.
    1. In the first image, at half the depth of the site, the dark existing forest occupies only about the LEFT ONE EIGHTH of the site's width; in the third image it occupies almost a third. Pull its ragged edge back to the LEFT so it again takes only the left one eighth at half depth. The forest still widens as it goes down, filling about the left third at the very bottom of the site, and it still runs off the left side of the slab.
    2. The strip freed by the forest becomes open light-green grass, so that there is a clear band of open grass between the forest edge and the WEST side of the timber boardwalk ring — the boardwalk must not be pressed against the trees.
    3. Move the RESERVOIR back to the WEST and make it a little narrower, so that it sits in the upper-LEFT quarter of the site as it does in the first image: its west shore close to the forest edge, and its east shore no further right than about the middle of the site's width. It still touches the stream, and the bird-watching hut still stands on its lower-right shore attached to the boardwalk.
    4. The stream still crosses the whole top of the site from left to right and passes behind the reservoir.

    NOTHING ELSE MOVES. The boardwalk ring, the wetland pond, the rest area, the gathering plaza, both entrance plazas, the straight path, the mound, the roads and the houses all stay exactly where they are, at exactly their present size.

    THE PROJECTION MUST STAY EXACTLY AS IT IS:
    - PARALLEL projection only. NO perspective, NO vanishing point, NO convergence anywhere.
    - The ground slab keeps exactly its present width, depth and foreshortening. Its far and near edges stay exactly HORIZONTAL and parallel; its left and right edges stay exactly VERTICAL and parallel. It is NOT wider at the near edge than at the far edge.
    - Every line running far-to-near in the plan — the right-hand road, the straight path, the dawn redwood row, the ginkgo row, the long mound — runs in one single direction and never converges with the others. Every line running left-to-right — the stream, the bottom road, the plaza kerbs — runs in one single other direction.
    - An object near the bottom of the picture is exactly the same size as the identical object near the top.
    - All vertical edges exactly vertical in the picture and exactly parallel to one another.
    - Same orientation: stream and reservoir at the TOP, dense forest on the LEFT and lower left, road and houses on the RIGHT, second road and houses along the BOTTOM RIGHT. Do not rotate, flip, zoom or mirror.

    EVERYTHING ELSE IS ALREADY CORRECT AND MUST BE REPRODUCED UNCHANGED: the reservoir's willows, reed beds and shoreline stones; the wetland pond with its reeds and stones; one closed angular timber boardwalk ring with EXACTLY 5 viewing platforms, each carrying one blank board; EXACTLY 1 bird-watching hut; the rest area with EXACTLY 1 pergola, 2 benches, 1 litter bin and its shade trees; the gathering plaza with EXACTLY 3 blank boards along its left edge and 1 tree in a square grate; the top-right entrance plaza with 2 trees in grates and 1 blank board; the bottom entrance plaza with 2 trees in grates and 1 blank board; five tree grates in all; the single row of about 12 dawn redwoods standing on grass beside the straight path; the long mound east of the path with 7 pines and azalea masses; the single ginkgo row inside the right-hand road continuing inside the bottom road; the multi-layered new woodland in the lower middle; the bottom road along the right half of the bottom edge only; the crisp site boundary; the shadows and the visible near-facing sides of every object.

    STRICT RULES: no new buildings, plazas, paths, bridges, fences, walls or car parks; every board and sign stays blank; NO text, letters, numbers, labels, legends, arrows, north arrow, scale bar, grid lines, dimension lines or watermark anywhere; no sky, no horizon, plain neutral background.
