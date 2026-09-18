'성운' 탭의 답안 도면과 문제지 조건을 GPT 이미지 모델(gpt-image-2.5-sunburst)에 주고 만든 **입체 조감도**입니다(1회차). 남동쪽 상공에서 북서쪽을 내려다본 시점이라 **도면의 북쪽이 그림의 위**입니다.

## 만든 방법

1. 기본설계도와 A−A′ 단면도를 참고로 주고 도면을 글로 풀어 쓴 프롬프트로 그렸습니다(1회차). 한 번에 입체 시점으로 도면과 맞게 나와 그대로 썼습니다

> 회차마다 도면을 첫 참고 그림으로 다시 주고, 앞 회차 그림을 둘째로 주어 "그것만 고치고 나머지는 그대로"라고 못박습니다. 마스크 부분 수정이나 손으로 자르고 돌리는 일은 하지 않습니다.

## 도면과 대조 (1회차)

| 도면(성운 답안) | 결과 |
| --- | --- |
| 북서 보행자전용도로(대각선), 남동 모따기 변에 20m 도로 · 버스정류장, 좌 · 상 아파트 | ✓ |
| +4.0 → 0 경사지를 단으로 나눠 계단 · 램프(8%)로 연결(지체장애인 고려) | ✓ |
| 중앙광장 — 수목보호대 · 장의자, 진입광장 2(북서 · 남동), 다목적공간 | ✓ |
| 휴게공간 3곳, 파고라 8 · 장의자 15 · 조명등 18 · 음수대 4 · 휴지통 4 | ✓ |
| 포장 2종 이상(화강석 · 소형고압블럭 · 자연석판석) | ✓ |
| 동선 주위 경계식재(회양목 · 산철쭉 띠), 잣나무 차폐, 은행 완충, 느티 · 벚 녹음 | ✓ |
| 글자 없음 | ✓ |

## 프롬프트 — 마지막 회차(1회차)

    Create a photorealistic 3D bird's-eye perspective rendering of the ENTRANCE PLAZA OF AN APARTMENT COMPLEX (아파트단지 진입광장) in central Korea. The FIRST attached image is the master plan (facilities + planting, hand-drawn Korean exam answer sheet); the SECOND is the A-A' section. Treat the drawing's TOP as "up" and describe positions as in the drawing. Reproduce the layout, shapes and positions faithfully; do not invent elements that are not in the plans.

    CAMERA: oblique aerial view from the drawing's LOWER-RIGHT corner looking toward the upper-left, tilted about 45 degrees (true 3D perspective), high enough that the whole site (about 60 x 60 m) plus the road at its lower-right is visible. Late-spring daylight, soft shadows.

    SITE: a roughly square plot whose UPPER-LEFT corner is cut by a diagonal PEDESTRIAN ROAD (a 6 m paved pedestrian-only street running from upper-left toward the centre-top) and whose LOWER-RIGHT corner is cut by a long 45° diagonal edge facing a 20 m ROAD (with a bus stop and the road beyond). Apartment blocks stand beyond the LEFT and TOP edges. The ground SLOPES DOWN from the upper-left (about +4 m) to the lower-right road (0 m), so the design is TERRACED: each terrace is flat and the terraces are linked by STEPS and RAMPS.

    LAYOUT (from the plan):
    1. CENTRAL PLAZA (중앙광장) at the centre of the site: a large square paved plaza (granite slabs) at an intermediate level, with a group of 4 square tree grates (zelkovas) at its upper-left, benches and lamps.
    2. Upper-left of the site, on the highest terrace beside the pedestrian road: an ENTRANCE PLAZA (진입광장) with a group of tree grates, reached from the pedestrian road; a RAMP (8%) and steps lead down from it to the central plaza.
    3. Lower-right: a second ENTRANCE PLAZA (진입광장) at the road, lowest level, with tree grates and a signboard, reached from the 20 m road; steps and a ramp climb from it to the central plaza; a MULTI-PURPOSE AREA (다목적공간) between them with benches.
    4. Upper-right: a REST AREA (휴게공간) with THREE timber PERGOLAS (4.5 x 4.5 m) in a row, benches and a drinking fountain, on a terrace at +3 m, edged with hedges.
    5. Left-centre and lower-left: two more REST AREAS, each with pergolas (the site has 8 pergolas in total), benches, lawns and hedge-lined paths; a curving planted slope with steps.
    6. Paths of interlocking blocks and natural flagstones connect all plazas; hedges of boxwood and azalea line every path (edge planting); 15 benches, 18 lamp posts, 4 drinking fountains, 4 trash bins in total.
    7. PLANTING: a screen of Korean pines along the top edge and the pedestrian road; ginkgos in a row along the outer (left) boundary; zelkovas and cherries as shade trees around the plazas and pergolas; maples and magnolias on the slopes; spiraea, privet, azalea and creeping juniper masses on the banks.

    STYLE: clean, realistic landscape-architecture visualization; terraces, steps and ramps clearly readable. Do NOT write any text, letters, numbers, labels or signs.
