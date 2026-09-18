'성운' 탭의 **답안지 II · 시설물배치도**와 **답안지 III · 배식평면도**, 문제지 조건을 AI 이미지 모델에 주고 만든 **입체 조감도**입니다(2026년 9월 18일).
위 사진의 첫 장이 **GPT**(gpt-image-2.5-sunburst, 7회차), 둘째 장이 **제미나이**(gemini-3-pro-image-preview, 2회차)입니다.

## 만든 방법 (GPT)

1. 도면 2장(시설물배치도 · 배식평면도, 표제란은 잘라냄)을 **참고 그림**으로 주고 **1회차 프롬프트**로 그렸습니다. 배치는 도면대로 나왔으나 거의 평면이었고, 남동 광장의 벤치 줄이 2개뿐이었습니다
2. **도면 + 1회차 그림**을 함께 주고 "배치는 그대로, 45° 입체 시점으로 다시 그리되 벤치 줄·녹지대 교목을 고치라"고 했습니다(2회차). 입체감이 생기고 배치도 유지됐습니다. 남은 것은 벤치 줄 3개(도면 6개), 삼각 화단 벤치 자리, 정원등, 볼라드 수
3. **도면 + 2회차 그림**을 주고 광장 가구의 **개수만** 고치게 했습니다(3회차) — 벤치 줄 3+3 과 휴지통·음수대, 삼각 화단 위 3 · 왼쪽 3, 정원등 3. 볼라드는 5개를 요구했는데 7개로 남았습니다
4. **북동 차량 출입구**를 도면과 대조하니(사용자 지적) 동측 녹지대와 보도가 끊기지 않아 차가 들어올 수 없었습니다. 도면은 북동 모서리 아래에 차량 진출입구, 그 위에 보행자 진출입구, 출입구 남쪽에 주차관리초소입니다. **도면 + 3회차 그림**을 주고 그 모서리만 열게 했습니다(4회차) — 동측 녹지대·보도를 가로지르는 진입로와 차단기, 그 북쪽에 보행 통로가 생겼습니다. 볼라드는 6개가 됐습니다
5. 4회차는 초소 **양쪽에 차단기**가 생겨 왼쪽 것이 순환 차로를 막았습니다. 도면을 다시 보니 **차단기 자체가 없고** 초소는 동측 녹지대 북쪽 끝에 붙어 있습니다(사용자 지적). 차단기를 모두 없애고 초소를 출입구 남쪽 녹지대 끝으로 옮기게 했습니다(5회차)
6. 5회차는 초소가 붙은 화단이 차로 쪽으로 **불룩 튀어나왔습니다**(사용자 지적). 녹지대 연석을 한 줄로 곧게 두고 초소를 그 폭 안에 넣게 했습니다(6회차)
7. **남서 출입구**도 같은 문제였습니다(사용자 지적) — 차단기가 있고 초소 화단이 차로로 튀어나왔으며, 서쪽 보행로 끝에 도면에 없는 초소가 하나 더 있었습니다. 차단기를 없애고 초소를 남측 녹지대 서쪽 끝 폭 안에 넣고, 군더더기 초소를 지우게 했습니다(7회차)

> **회차마다 도면을 첫 참고 그림으로 다시 준다.** 앞 회차 그림만 주면 기준이 흐려져 조금씩 어긋납니다.
> **마스크로 일부만 고치거나 그림을 손으로 자르고 돌리지 않는다.** 그 방법으로 한 앞선 시도는 장애인 주차칸을 옆 주차열에 맞춘다고 옮기다 순환 차로를 막고, 비스듬한 조감도에서 칸만 수평으로 세워 오히려 주변과 어긋나게 만들었습니다. 틀리면 도면과 함께 **통째로 다시 그리게** 하는 편이 확실합니다

## 도면과 대조 (GPT 7회차)

| 도면(성운 답안) | 결과 |
| --- | --- |
| 107m × 150m 부지, 남동 모서리 45° 모따기, 모서리 밖 보도에 지하철 출입구 | ✓ |
| 주차열 4줄(북쪽 2줄 길고 남쪽 2줄 짧음), 열마다 가운데 녹지 · 녹음수 · 양 끝 둥근 화단 | ✓ |
| 주차장을 도는 순환 차로 — 장애인 주차칸 서쪽 남북 차로가 남쪽 가장자리까지 열림 | ✓ |
| 장애인 주차 8칸 — 3번째 열 동쪽, 그 열 위쪽 칸과 같은 줄, 북쪽 차로로 열림 | ✓ |
| 서측 보행로 + 주차 1줄, 북 · 서측 12m 상록 차폐 띠, 남 · 동측 6m 가로수 | ✓ |
| 북서 휴게광장(퍼걸러 2 · 격자 수목보호대), 북측 화장실, 주차관리소 북동 · 남서 | ✓ |
| 북동 차량 진출입구 — 동측 광로에서 녹지대 · 보도를 끊고 들어오는 진입로, 그 북쪽 보행 진출입구 | ✓ (4~6회차에 고침) — 차단기 없음, 초소는 동측 녹지대 북쪽 끝에 붙어 연석이 곧게 이어짐 |
| 남서 차량 진출입구 — 남측 광로에서 들어오는 진입로, 초소는 남측 녹지대 서쪽 끝, 그 서쪽에 보행 진출입구 | ✓ (7회차에 고침) — 차단기 없음, 연석 곧음, 도면에 없던 초소 하나 지움 |
| 남동 광장 — 장애인 주차 아래 녹지대(교목 6 · 정원등 3), 벤치 3 + 휴지통 · 음수대 + 벤치 3 | ✓ |
| 남동 광장 — 직각삼각형 화단(위 벤치 3 · 왼쪽 벤치 3), 북동 · 남서 모서리 체크무늬 포장 | ✓ |
| 남동 광장 서측 볼라드 5 | **6개** — 세 번 요구해 7 → 6 |
| 북측 주거지 · 서측 상업지 · 남 · 동측 광로, 글자 없음 | ✓ |

비용은 GPT 3장 약 $0.12, 제미나이 2장 약 $0.26 입니다.

## 프롬프트 — 마지막 회차(7회차, GPT · 참고: 시설물배치도 + 6회차 그림)

앞 회차 그림을 함께 주고 "그 모서리만 고치고 나머지는 그대로"라고 한 것입니다. 1~6회차 프롬프트는 뺐습니다.

    The FIRST attached image is the facilities plan of a parking park (north is up). The SECOND attached image is a 3D rendering of it that is correct in layout and camera. Reproduce the second image EXACTLY — same camera, perspective, parking rows, trees, buildings, plazas, roads, subway entrance, lighting, and the already-correct north-east entrance — and change ONLY the SOUTH-WEST corner, to match the plan:

    1. REMOVE ALL BARRIER ARMS / GATES at the south-west vehicle entrance. The plan has none. The entrance is an open asphalt driveway running north-south from the south boulevard into the ring aisle, with a dropped curb at the sidewalk.

    2. The south-west parking attendant booth (small 4 x 4 m square hut) must sit INSIDE the width of the SOUTH planting strip at its WEST end — flush with the strip, its north wall on the same straight line as the strip's north curb. Right now the booth stands on a rounded planting bed that BULGES NORTH into the ring aisle: remove that bulge so the strip keeps one straight east-west curb line and the aisle runs straight at full width. The driveway is directly WEST of the booth.

    3. REMOVE the second small hut / gate standing further west at the foot of the west pedestrian walkway; the plan has only a plain pedestrian opening there (block-paved path from the walkway to the south sidewalk), no building.

    Nothing else changes. Photorealistic landscape-architecture visualization. Do NOT write any text, letters, numbers, labels or signs.
