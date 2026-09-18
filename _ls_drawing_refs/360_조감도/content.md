'성운' 탭의 답안 도면과 문제지 조건을 GPT 이미지 모델(gpt-image-2.5-sunburst)에 주고 만든 **입체 조감도**입니다(2회차). 남동쪽 상공에서 북서쪽을 내려다본 시점이라 **도면의 북쪽이 그림의 위**입니다.

## 만든 방법

1. 기본설계도 · 식재설계도 2장을 참고로 주고 도면을 글로 풀어 쓴 프롬프트로 그렸습니다(1회차). 노인정 · 놀이공간(조합놀이대 · 고무매트) · 다목적 운동공간(배드민턴장 · 마사토) · 포장광장(파고라 · 수목보호대) · 휴게공간(파고라) · 마운딩 녹지와 산책로 · 십자 주동선이 도면대로 나왔으나 시점이 평면이었습니다
2. 도면 + 1회차 그림을 주고 45° 입체 시점으로 다시 그리게 했습니다(2회차)

> 회차마다 도면을 첫 참고 그림으로 다시 주고, 앞 회차 그림을 둘째로 주어 "그것만 고치고 나머지는 그대로"라고 못박습니다. 마스크 부분 수정이나 손으로 자르고 돌리는 일은 하지 않습니다.

## 도면과 대조 (2회차)

| 도면(성운 답안) | 결과 |
| --- | --- |
| 75×40 부지, 네 변 도로(12m · 8m)와 주택지, 주동선 5m 십자 · 부동선 2m | ✓ |
| 노인정 6×15 서측 좌상 가로형 | ✓ |
| 어린이 놀이공간 18×18 서측 좌하, 조합놀이대, 고무매트 | ✓ |
| 다목적 운동공간 18×17 중앙, 배드민턴장, 마사토 | ✓ |
| 포장광장 210m² 동측 중앙 위, 화강석판석, 파고라 1 · 수목보호대 1 | ✓ |
| 휴게공간 파고라 1, 등의자 12 | ✓ |
| 녹지 4m 이상 상 · 하 · 우측, 마운딩, 산책로(투수콘) | ✓ |
| 잣나무 · 향나무 도로변, 은행 · 느티 동선, 일본목련 · 단풍 · 벚 마운딩, 개나리 · 철쭉 | ✓ |
| 글자 없음 | ✓ |

## 프롬프트 — 마지막 회차(2회차)

    The FIRST attached image is the facilities plan of a small neighbourhood park (drawing's top = up). The SECOND attached image is a rendering of it whose LAYOUT is correct: keep every element in exactly the same place — the senior centre at upper-left, the rubber-mat playground with the combined play structure at lower-left, the sandy badminton court in the centre, the paved plaza with a pergola and tree grate at upper-right, the rest area with the second pergola at right-centre, the mounded greens with the winding trail along the top, bottom and right, the crossing main walks, the four streets and houses around.

    Change ONLY the camera: image 2 is a flat top-down view. Re-render the same layout as a TRUE 3D OBLIQUE PERSPECTIVE from the drawing's lower-right, looking toward the upper-left, tilted about 45 degrees, at roughly 70 m height, so the senior centre, pergolas, play structure, mounds and trees show their height and sides and the far (upper-left) side appears smaller than the near side. Long soft late-afternoon shadows.

    Everything else exactly as in image 2. Photorealistic landscape-architecture visualization. Do NOT write any text, letters, numbers, labels or signs.
