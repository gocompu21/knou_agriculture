'성운' 탭의 **답안지 II · 기본설계도**와 **답안지 III · 배식설계도**, 문제지 조건을 GPT 이미지 모델(gpt-image-2.5-sunburst)에 주고 만든 **입체 조감도**입니다(2026년 9월 18일, 4회차).
남동쪽 상공에서 북서쪽을 내려다본 시점이라 **도면의 북쪽이 그림의 위**입니다 — 실개천이 위, 기존수림이 왼쪽, 6m 도로와 주택가가 오른쪽·아래입니다.

## 만든 방법

1. 도면 2장(기본설계도 · 배식설계도, 표제란은 잘라냄)을 참고 그림으로 주고 도면을 글로 풀어 쓴 프롬프트로 그렸습니다(1회차). 배치는 도면대로 나왔고, 남측 도로가 부지 전체 폭으로 그려진 것과 휴게공간 평의자·모임광장 안내판이 모자란 것만 틀렸습니다
2. **도면 + 1회차 그림**을 함께 주고 그 셋만 고치게 했습니다(2회차) — 남측 도로를 동쪽 절반으로 줄이고(서쪽은 야산), 평의자 8 · 휴지통 1, 안내판을 더했습니다
3. **도면 + 2회차 그림**을 주고 모임광장 서쪽 안내판을 3개로, 관찰데크를 5개로 맞추게 했습니다(3회차)
4. **북동 진입광장**을 도면과 대조하니(사용자 지적) 동선 동쪽 잔디에 메타세쿼이아 열이 하나 더 들어가 있고, 종합안내판이 북쪽 변에, 광장과 동측 도로 사이에 나무가 끼어 있었습니다. 배식설계도대로 그 잔디를 **마운딩 + 소나무 7주 + 철쭉**으로, 안내판을 서쪽 변으로, 광장이 도로로 바로 열리게 고쳤습니다(4회차)

> 회차마다 도면을 첫 참고 그림으로 다시 주고 "나머지는 그대로"라고 못박습니다. 마스크 부분 수정이나 그림을 손으로 자르고 돌리는 일은 하지 않습니다(주차장 설계 444 조감도 탭 참조).

## 도면과 대조 (4회차)

| 도면(성운 답안) | 결과 |
| --- | --- |
| 북쪽 실개천 · 서쪽 기존수림 · 동쪽과 남동쪽 6m 도로와 주택가, 남서쪽은 야산 | ✓ (남측 도로는 2회차에 동쪽 절반으로 고침) |
| 저수지구 — 북서쪽, 실개천에 붙은 자연형 연못, 남동 물가에 조류관찰소 5×4 + 안내판 | ✓ |
| 습지지구 — 가운데, 자연형 호안의 작은 연못, 부들·갈대·골풀 | ✓ |
| 목재데크 관찰로가 습지를 다각형으로 한 바퀴, 관찰데크 5 · 안내판 5, 서·남쪽 두 구간은 석판 포장 | ✓ |
| 산림지구 — 남서쪽, 기존수림과 이어지는 다층 숲, 관찰로, 수목표찰 10 | ✓ (표찰은 작은 말뚝으로) |
| 휴게공간 — 산림지구 남동 가장자리, 파고라 4×4 · 평의자 8 · 휴지통 1 | ✓ (2회차에 고침) |
| 모임광장 — 습지 동쪽, 수목보호대 1, 서쪽 안내판 3 | ✓ (3회차에 고침) |
| 진입광장 2 — 북동 모서리 · 남쪽(남동 근처), 종합안내판 1 · 수목보호대 2씩, 소형고압블록 | ✓ (북동 광장은 4회차에 고침 — 도로로 바로 열림, 안내판 서쪽 변) |
| 두 진입광장을 잇는 남북 동선, 서쪽 메타세쿼이아 열식, 동쪽 마운딩에 소나무 7 · 철쭉, 도로변 은행나무 열식 | ✓ (4회차에 고침) |
| 글자 없음 | ✓ |

비용은 3장 약 $0.12 입니다.

## 프롬프트 — 마지막 회차(4회차, 참고: 기본설계도 + 3회차 그림)

앞 회차 그림을 함께 주고 "그것만 고치고 나머지는 그대로"라고 한 것입니다. 1~3회차 프롬프트는 뺐습니다.

    The FIRST attached image is the site plan of a small ecological park (north is up). The SECOND attached image is a 3D rendering of it that is correct in layout and camera. Reproduce the second image EXACTLY — same camera, pond, wetland, boardwalk loop, forest, pergola plaza, gathering plaza, south entrance plaza, stream, roads, houses, lighting — and change ONLY the NORTH-EAST corner and the lawn south of it, to match the plan:

    1. NORTH-EAST ENTRANCE PLAZA (block-paved square at the north-east corner): its EAST edge opens DIRECTLY onto the east road with a dropped curb — no trees, hedge or planting strip between the plaza and the road; people walk straight in from the road. Its 2 square tree grates (each with one zelkova) stay, one north and one south of the plaza's centre. The large blank signboard stands on the plaza's WEST edge (not on the north edge). A row of ginkgo trees runs along the north edge of the site above the plaza.

    2. LAWN between the north-south block path and the east road (south of the entrance plaza): remove the line of tall narrow conifers standing in the MIDDLE of this lawn. Instead the lawn has a gentle grassy MOUND (a low rounded hump) planted with 7 spreading PINE trees (round, dark-green, irregular crowns — not columnar) and irregular masses of low azalea shrubs. The line of ginkgo trees along the road edge stays. The single line of metasequoias along the WEST side of the north-south path (between the path and the wetland boardwalk) stays.

    Nothing else changes. Photorealistic landscape-architecture visualization. Do NOT write any text, letters, numbers, labels or signs.
