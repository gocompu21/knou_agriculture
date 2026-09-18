'성운' 탭의 답안 도면과 문제지 조건을 GPT 이미지 모델(gpt-image-2.5-sunburst)에 주고 만든 **입체 조감도**입니다(2회차). 남동쪽 상공에서 북서쪽을 내려다본 시점이라 **도면의 북쪽이 그림의 위**입니다.

## 만든 방법

1. 시설물배치도 · 배식평면도 2장을 참고로 주고 도면을 글로 풀어 쓴 프롬프트로 그렸습니다(1회차). 모따기된 왼쪽 모서리의 주차장과 참나무 총림, 위쪽 농구장과 화장실, 가운데 잔디광장(스탠드 · 수목보호대 10), 왼쪽 아래 모험놀이공간, 목재데크 휴식공간(파고라 2)과 연못, 오른쪽 아래 곡선 산책로와 RAMP, 오른쪽 주동선이 도면대로 나왔으나 시점이 평면에 가까웠습니다
2. 도면 + 1회차 그림을 주고 45° 입체 시점으로 다시 그리게 했습니다(2회차)

> 회차마다 도면을 첫 참고 그림으로 다시 주고, 앞 회차 그림을 둘째로 주어 "그것만 고치고 나머지는 그대로"라고 못박습니다. 마스크 부분 수정이나 손으로 자르고 돌리는 일은 하지 않습니다.

## 도면과 대조 (2회차)

| 도면(성운 답안) | 결과 |
| --- | --- |
| 오각형 부지(왼쪽 모따기), 둘레 3m 보행로와 도로, 위 상가 · 오른쪽 아파트 · 왼쪽 주택 | ✓ |
| 법면 1:1.8, 차량진입 2곳(위 · 왼쪽 아래 사선) 17%, 보행진입 2곳(오른쪽 위 · 아래) | ✓ |
| 주차 26대 직각, 안전동선 1.5m, 아스콘 · 북쪽 참나무 총림 40주 | ✓ |
| 농구장 15×28 우레탄, 벤치 4곳 8개, 생울타리 · 편익공간 7×26에 화장실 5×7 | ✓ |
| 잔디광장 32×17 −60cm, 둘레 스탠드, 활동공간 3~6m(진입부 12m), 수목보호대 10 | ✓ |
| 모험놀이공간 300m² 탄성고무, 놀이시설 3종 | ✓ |
| 휴식공간 목재데크 10×12, 파고라 2 · 음수대 · 휴지통, 연못 80m² 자연석 경계 | ✓ |
| 산책로 2m 자유곡선 콘크리트 10%, RAMP 8% + 계단 | ✓ |
| 잣나무 · 벚나무 외곽, 느티 · 참나무 광장 둘레, 단풍 · 산철쭉 · 옥향 법면 | ✓ |
| 글자 없음 | ✓ |

## 프롬프트 — 마지막 회차(2회차)

    The FIRST attached image is the facilities plan of a neighbourhood park (drawing's top = up). The SECOND attached image is a rendering of it whose LAYOUT is correct: keep every element in exactly the same place — the chamfered left corner with the parking lot and oak grove, the basketball court and toilet at the top, the sunken lawn plaza with its stepped stands and the ten tree grates, the adventure playground at lower-left, the timber deck with two pergolas and the pond, the winding trail and the ramp at lower-right, the main path along the right edge, the streets, shops, apartments and houses around.

    Change ONLY the camera: image 2 is almost a flat top-down view. Re-render the same layout as a TRUE 3D OBLIQUE PERSPECTIVE from the drawing's lower-right, looking toward the upper-left, tilted about 45 degrees, at roughly 90 m height, so the buildings, pergolas, play structures, trees and the sunken plaza's steps show their height and sides and the far (upper-left) side of the site appears smaller than the near side. Long soft late-afternoon shadows.

    Everything else exactly as in image 2. Photorealistic landscape-architecture visualization. Do NOT write any text, letters, numbers, labels or signs.
