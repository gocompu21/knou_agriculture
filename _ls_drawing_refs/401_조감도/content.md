'성운' 탭의 **답안지 II · 기본설계도**와 **답안지 III · 배식설계도**, 문제지 조건으로 만든 **입체 조감도**입니다.
**GPT**(gpt-image-2.5-sunburst, 9회차)로 그렸습니다. 남동쪽 상공에서 북서쪽을 내려다본 시점이라 **도면의 북쪽이 그림의 위**입니다 —
실개천이 위, 기존수림이 왼쪽, 6m 도로와 주택가가 오른쪽·아래입니다.

## 만든 방법 — 1회차 그림에서 **한 번에**

1. 도면 2장(기본설계도 · 배식설계도, 표제란은 잘라냄)을 참고 그림으로 주고 도면을 글로 풀어 쓴 프롬프트로 그렸습니다(1회차).
   배치는 도면대로 나왔고 **화질이 가장 좋았습니다**(선명도 2586)
2. 2~6회차는 틀린 곳을 **한두 개씩 차례로** 고쳤습니다 — 남측 도로를 동쪽 절반으로, 휴게공간 평의자·휴지통, 관찰데크 5개,
   모임광장 안내판, 북동 진입광장(마운딩·소나무·안내판 위치·수목보호대 2개), 남측 진입광장(도로와 평행한 직사각형).
   배치는 맞아 갔지만 **덧그릴 때마다 화질이 깎여** 6회차에는 선명도가 **542**까지 떨어졌습니다(1회차의 21%).
   7회차에 동측 도로를 동선과 평행하게 고쳐 봤으나 사용자가 기각했습니다
3. 그래서 **6회차 위에 더 얹지 않고 1회차로 돌아가**, 2~6회차에서 고쳤던 것과 새로 지적된 것을 **모두 한 프롬프트에 넣어
   한 번에** 그렸습니다(8·9회차). 선명도가 **2945** 로 1회차보다도 높아졌습니다 — 배포본 542 의 **5.4배**입니다
4. 8회차에서 ①~⑪이 모두 맞았고, 안내판의 **흰 판이 멀리서 흰 점으로 도드라진다**는 지적이 남아
   9회차에 ⑫ "틀 안을 짙은 나뭇결 목재판으로, 주변 잔디·포장보다 어둡게"를 더했습니다.
   판면 밝기를 재 보니 **102 : 주변 포장 162** 로 확실히 어둡습니다(8회차는 168 : 148 로 오히려 밝았습니다)

> **덧그리기는 곧 화질입니다.** 고칠 것이 생기면 마지막 그림 위에 얹지 말고, **덧그림이 적은 앞 회차로 돌아가
> 고칠 것을 모두 한 프롬프트에 모아** 다시 그리는 편이 낫습니다. 같은 방식으로 'My' 탭 조감도와 '입체평면도'도 고쳤습니다.
> 마스크 부분 수정이나 그림을 손으로 자르고 돌리는 일은 하지 않습니다.

## 도면과 대조 (9회차)

| 도면(성운 답안) | 결과 |
| --- | --- |
| 북쪽 실개천 · 서쪽 기존수림 · 동쪽과 남동쪽 6m 도로와 주택가, 남서쪽은 야산 | ✓ 남측 도로는 부지 **동쪽 절반만** |
| 저수지구 — 북서쪽, 실개천에 붙은 자연형 연못, 남동 물가에 조류관찰소 5×4 + 안내판 | ✓ |
| 습지지구 — 가운데, 자연형 호안의 작은 연못, 부들·갈대·골풀 | ✓ |
| 목재데크 관찰로가 습지를 다각형으로 한 바퀴, 관찰데크 5 · 안내판 5 | ✓ 안내판 합계 6(관찰데크 5 + 조류관찰소 1) |
| 산림지구 — 남서쪽, 기존수림과 이어지는 다층 숲, 관찰로, 수목표찰 | ✓ |
| 휴게공간 — 파고라 4×4 1 · **평의자 5** · 휴지통 1 | ✓ |
| 모임광장 — 습지 동쪽, 수목보호대 1 · **평의자 3** | ✓ 시설물 수량표가 평의자 8 · 안내판 6 · 종합안내판 1 인데 안내판 6은 관찰데크 5 + 조류관찰소 1 로 다 차므로, 평의자 8 − 휴게공간 5 = 3 이 모임광장 몫입니다 |
| 진입광장 2 — 북동 모서리 · 남측, 종합안내판 1 · 수목보호대 2씩, 소형고압블록 | ✓ 안내판은 서쪽 변, 광장이 도로로 바로 열림. 북동 광장 북쪽 은행나무는 보호대 없이 녹지에 |
| 두 진입광장을 잇는 남북 동선, 서쪽 메타세쿼이아 열식, 동쪽 마운딩에 소나무 7 · 철쭉, 도로변 은행나무 열식 | ✓ 마운딩은 **봉긋한 잔디 둔덕**이고 서쪽 변과 남쪽 변을 따라 **끊기지 않는 꽃관목 띠**를 둘렀습니다 |
| 안내판 판면 | ✓ 짙은 나뭇결 목재판 — 주변 포장보다 어둡습니다(102 : 162) |
| 글자 없음 | ✓ |

비용은 9장 약 $0.39 입니다(8·9회차만 `xhigh` 품질이라 장당 $0.074).

## 프롬프트 — 마지막 회차(9회차, 참고: 기본설계도 + 배식설계도 + 1회차 그림)

1회차 그림을 함께 주고 고칠 열두 가지를 한꺼번에 적은 것입니다. 1~8회차 프롬프트는 뺐습니다.

    The FIRST attached image is the site and facilities plan of a small Korean ecological park (north is up in the drawing). The SECOND attached image is the planting plan of the same site. These two drawings are the ground truth for WHAT is where.

    The THIRD attached image is a photorealistic bird's-eye rendering of that park. Its CAMERA, its PERSPECTIVE, its FRAMING, its DAYLIGHT, its MATERIALS, its TEXTURES and its SHARPNESS are all EXACTLY RIGHT, and so is the overall layout. Copy all of that.

    Redraw the third image, fresh and sharp, changing ONLY the twelve things listed below so that it matches the two drawings. Nothing else changes.

    1. SOUTH ROAD — EAST HALF ONLY. The 6 m residential road along the bottom edge must run ONLY along the EASTERN HALF of that edge, from the south entrance plaza east to the corner. Along the WESTERN HALF there is NO road at all: the park's forest runs straight on into the wooded hill beyond. Delete the western part of the road and its kerbs and fill that ground with woodland.

    2. REST AREA. The small paved square beside the pergola, at the south-east edge of the forest, must hold EXACTLY 1 timber pergola, EXACTLY 5 flat backless timber benches standing on the paving around it, all five clearly visible and none hidden under the pergola roof, and EXACTLY 1 round litter bin. Count the benches: one, two, three, four, five.

    3. BOARDWALK DECKS. The timber boardwalk loop round the marsh must carry EXACTLY 5 small observation decks bulging outward from it, each one a small timber platform with rails and ONE small board with a dark timber panel. Count them: one, two, three, four, five.

    4. NORTH-EAST ENTRANCE PLAZA. It sits at the top-right corner and must open DIRECTLY onto the east road with a dropped kerb — nothing stands between the plaza and the road. Its large signboard stands on the plaza's WEST edge facing east, not on its north edge.

    5. TREE GRATES THERE. That plaza has EXACTLY 2 square tree grates, each with one shade tree, and no more. The line of yellow-green ginkgo trees along the north side of the plaza grows in open planted ground, NOT in tree grates — give them no grates at all.

    6. SOUTH ENTRANCE PLAZA. It must be a clean RECTANGLE whose edges are exactly parallel and perpendicular to the south road and the east road — no diagonal or tapered edge. Its south edge opens straight onto the south road. EXACTLY 1 large signboard stands on its WEST edge facing east; nothing stands on its east side. The straight north-south block-paved path arrives at it running exactly north-south.

    7. THE MOUND'S MISSING SHRUB EDGING. The long grassy mound lies in the lawn between the straight north-south path and the ginkgo row along the east road. Its WEST edge, where the turf meets the block paving of the path, is at present bare grass. Plant a CONTINUOUS BAND OF LOW FLOWERING SHRUBS along it: one unbroken ribbon of dense, rounded, knee-high flowering shrubs, two or three deep, hugging the turf edge. It starts at the mound's north end and runs all the way to its south end WITHOUT A SINGLE GAP, and at the south end it TURNS and runs along the mound's south edge as well, so the ribbon makes an L. Its outer line is soft and lobed, never a clipped straight hedge.

    8. THE MOUND IS A ROUNDED GRASSY HILL. It must read as ground that SWELLS UPWARD: from the surrounding lawn it rises smoothly to a long rounded crest down its middle, lit on top and shading gradually as it falls away to the sides, with a soft shadow on the lawn. There is NO dark outline ring, no kidney-shaped border, no kerb, no trench, no step and no mowing stripe drawn on it. Its turf is the same turf as the lawn and runs on into it with no visible join. It carries EXACTLY 7 spreading pines with broad masses of pink azaleas between them.

    9. GATHERING PLAZA — THREE BENCHES, NO BOARDS. The gathering plaza is the paved square on the east side of the marsh where the boardwalk loop meets the paths, the one with a single shade tree growing in a square tree grate. On its WEST edge, in the strip of paving between the timber boardwalk deck and that tree, stand EXACTLY 3 flat backless BROWN TIMBER BENCHES in a row, evenly spaced, all identical. Count them: one bench, two benches, three benches. There is NO signboard, NO upright panel and NO standing board of any kind anywhere on this plaza.

    12. THE BOARD FACES ARE DARK TIMBER, NOT WHITE. Every signboard in the picture - the 5 small boards on the observation decks, the 1 board beside the bird-watching hide, and the large boards on both entrance plazas - currently has a BRIGHT WHITE face inside its timber frame, so it stands out as a white dot from far away. Replace that white face with a panel of DARK, GRAIN-TEXTURED TIMBER. The panel must be DARKER than the grass and darker than the block paving around it; never white, never light grey, never pale. Put only a few very faint lines on it and NO letters and NO text of any kind. Keep the timber frame and its legs exactly as they are - you are changing only the COLOUR AND MATERIAL OF THE PANEL, you are NOT removing any signboard. All of them still stand where they stand.

    10. THE OTHER BOARDS ALL STAY. The 5 small blank boards on the 5 observation decks and the 1 blank board beside the timber bird-watching hide at the pond must ALL be there — SIX boards in all, each now with a dark timber panel. Do not delete them, do not move them and do not turn them into benches. The large signboards on the two entrance plazas also stay.

    11. BOARDS STAND SQUARE. Every remaining signboard stands square to the paving or deck it is on: the long edge of each board is exactly PARALLEL to the edge of that paving or deck, and its face looks straight out across it. Not one board is left skewed or turned at an odd angle.

    WHAT MUST NOT CHANGE:
    - The same camera and the same true perspective: an oblique aerial view from the SOUTH-EAST looking north-west, tilted about 45 degrees, with the stream at the top of the picture. The same framing and crop, the same late-spring daylight and soft shadows, the same colour balance.
    - The EAST ROAD keeps exactly the angle it has in the third image. Do NOT rotate it, do NOT make it parallel to the north-south path, do NOT straighten it.
    - The rectangular site and its surroundings: the rocky stream along the whole north edge with a wooded hill beyond; dense existing woodland filling the west side and the south-west; the 6 m road with low-rise houses along the east edge.
    - The reservoir pond in the north-west with its rocky, reedy shoreline and its willows; the timber bird-watching hide on its south-east shore; the marsh with its kidney-shaped pool, cattails, rushes and reeds and its soft planted bank; the angular timber boardwalk loop on posts with low rails.
    - The multi-layered forest in the south-west with its winding earth trail; the block-paved gathering plaza and the two entrance plazas; the straight north-south block-paved path; the two lines of tall metasequoias flanking that path; the single row of yellow-green ginkgos along the east road; the willows, dogwoods, spiraea and wild roses at the water's edge.

    RENDER IT FRESH AT MAXIMUM RESOLUTION AND MAXIMUM DETAIL — this matters as much as the twelve fixes. Draw the whole picture again; do not retouch, soften or resample the third image. Every part must be at least as crisp and as finely detailed as the third image: the individual leaves in every canopy, the blades of the turf, the grain and board joints of the boardwalk, the individual blocks of the paving, the rocks at the water's edge, the roof tiles of the houses. Do not simplify, smooth or average any texture.

    STRICT RULES: no new buildings, plazas, paths, bridges, fences, walls, cars or people; every board carries a dark timber panel with no writing on it; NO text, letters, numbers, labels, legends, arrows, north arrow, scale bar, grid lines, dimension lines or watermark anywhere in the picture.
