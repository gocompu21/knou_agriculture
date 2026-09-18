'성운' 탭의 답안 도면과 문제지 조건을 GPT 이미지 모델(gpt-image-2.5-sunburst)에 주고 만든 **입체 조감도**입니다(2회차). 남동쪽 상공에서 북서쪽을 내려다본 시점이라 **도면의 북쪽이 그림의 위**입니다.

## 만든 방법

1. 시설물배치도 · 배식평면도 2장을 참고로 주고 도면을 글로 풀어 쓴 프롬프트로 그렸습니다(1회차). 접근로 · 북서 주차장(동서 3열 · 화단 녹음식재 · 장애인 4) · 관리사무소와 쓰레기수거장 · 남서 연못과 계곡 · 가운데 잔디광장 · 화장실&샤워실 2(북) · 개수대 2(남) · 순환 보행로 · 목재데크 야영사이트 30 · 동측 완충녹지가 도면대로 나왔으나 시점이 평면에 가까웠습니다
2. 도면 + 1회차 그림을 주고 45° 입체 시점으로 다시 그리고 진입광장(6×40m, 수목보호대 3 · 안내표지판)을 또렷이 하게 했습니다(2회차)

> 회차마다 도면을 첫 참고 그림으로 다시 주고, 앞 회차 그림을 둘째로 주어 "그것만 고치고 나머지는 그대로"라고 못박습니다. 마스크 부분 수정이나 손으로 자르고 돌리는 일은 하지 않습니다.

## 도면과 대조 (2회차)

| 도면(성운 답안) | 결과 |
| --- | --- |
| 서쪽 비스듬한 접근로 · 기존수림, 남서 계곡, 북쪽 산책로 | ✓ |
| 북서 주차장 — 직각주차 장축 남북 3열, 순환형, 소형 50 · 장애인 4, 아스팔트, 쉐도우파킹 녹음수 | ✓ |
| 관리사무소 3×3 · 쓰레기수거장 10×5 · 안내표지판 | ✓ |
| 남서 연못 600m² 이상 + 둘레 마사토 산책로, 갈대 · 수련 · 갯버들 | ✓ |
| 진입광장 6×40 남북, 수목보호대 3 | ✓ |
| 잔디광장 25×25 + 2m 산책로, 3m 순환 보행로(소형고압블럭) | ✓ |
| 화장실&샤워실 2(잔디광장 북) · 개수대 2(남) 대칭 | ✓ |
| 야영사이트 6×6 목재데크 30, 사이 3m 마사토, 전기분전반, 벤치 4 | ✓ |
| 동측 7m 완충녹지(굴참 · 잣나무), 진입광장-야영장 사이 대형교목 완충, 입구 소나무 | ✓ |
| 글자 없음 | ✓ |

## 프롬프트 — 마지막 회차(2회차)

    The FIRST attached image is the facilities plan of a campground (north is up). The SECOND attached image is a rendering of it whose LAYOUT is correct: keep every element in exactly the same place — the diagonal access road and woodland on the left, the asphalt parking lot with three east-west double rows and planted medians, the office and waste shelter south of it, the pond with its sandy path and the stream valley in the south-west, the central lawn plaza with two toilet/shower buildings north of it and two washing-up shelters south of it, the block-paved loop road, the thirty square timber camping decks with tents, and the forest buffer on the east.

    Change these two things only:
    1. CAMERA — image 2 is almost a flat top-down view. Re-render the same layout as a TRUE 3D OBLIQUE PERSPECTIVE from the south-east looking north-west, tilted about 45 degrees, at roughly 120 m height, so buildings, tents, trees and the parking medians show their height and sides and the far (north-west) side appears smaller than the near (south-east) side. Long soft late-afternoon shadows.
    2. The narrow north-south ENTRANCE PLAZA between the parking lot and the camping area (6 m wide, 40 m long, grey interlocking blocks) must clearly show 3 square tree grates in a line, each with one shade tree, and one large blank signboard at its north end.

    Everything else exactly as in image 2. Photorealistic landscape-architecture visualization. Do NOT write any text, letters, numbers, labels or signs.
