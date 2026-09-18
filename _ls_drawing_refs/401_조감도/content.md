'성운' 탭의 **답안지 II · 기본설계도**와 **답안지 III · 배식설계도**, 문제지 조건을 GPT 이미지 모델(gpt-image-2.5-sunburst)에 주고 만든 **입체 조감도**입니다(2026년 9월 18일, 3회차).
남동쪽 상공에서 북서쪽을 내려다본 시점이라 **도면의 북쪽이 그림의 위**입니다 — 실개천이 위, 기존수림이 왼쪽, 6m 도로와 주택가가 오른쪽·아래입니다.

## 만든 방법

1. 도면 2장(기본설계도 · 배식설계도, 표제란은 잘라냄)을 참고 그림으로 주고 도면을 글로 풀어 쓴 프롬프트로 그렸습니다(1회차). 배치는 도면대로 나왔고, 남측 도로가 부지 전체 폭으로 그려진 것과 휴게공간 평의자·모임광장 안내판이 모자란 것만 틀렸습니다
2. **도면 + 1회차 그림**을 함께 주고 그 셋만 고치게 했습니다(2회차) — 남측 도로를 동쪽 절반으로 줄이고(서쪽은 야산), 평의자 8 · 휴지통 1, 안내판을 더했습니다
3. **도면 + 2회차 그림**을 주고 모임광장 서쪽 안내판을 3개로, 관찰데크를 5개로 맞추게 했습니다(3회차)

> 회차마다 도면을 첫 참고 그림으로 다시 주고 "나머지는 그대로"라고 못박습니다. 마스크 부분 수정이나 그림을 손으로 자르고 돌리는 일은 하지 않습니다(주차장 설계 444 조감도 탭 참조).

## 도면과 대조 (3회차)

| 도면(성운 답안) | 결과 |
| --- | --- |
| 북쪽 실개천 · 서쪽 기존수림 · 동쪽과 남동쪽 6m 도로와 주택가, 남서쪽은 야산 | ✓ (남측 도로는 2회차에 동쪽 절반으로 고침) |
| 저수지구 — 북서쪽, 실개천에 붙은 자연형 연못, 남동 물가에 조류관찰소 5×4 + 안내판 | ✓ |
| 습지지구 — 가운데, 자연형 호안의 작은 연못, 부들·갈대·골풀 | ✓ |
| 목재데크 관찰로가 습지를 다각형으로 한 바퀴, 관찰데크 5 · 안내판 5, 서·남쪽 두 구간은 석판 포장 | ✓ |
| 산림지구 — 남서쪽, 기존수림과 이어지는 다층 숲, 관찰로, 수목표찰 10 | ✓ (표찰은 작은 말뚝으로) |
| 휴게공간 — 산림지구 남동 가장자리, 파고라 4×4 · 평의자 8 · 휴지통 1 | ✓ (2회차에 고침) |
| 모임광장 — 습지 동쪽, 수목보호대 1, 서쪽 안내판 3 | ✓ (3회차에 고침) |
| 진입광장 2 — 북동 모서리 · 남쪽(남동 근처), 종합안내판 1 · 수목보호대 2씩, 소형고압블록 | ✓ |
| 두 진입광장을 잇는 남북 동선, 양쪽 메타세쿼이아 열식, 도로변 은행나무 열식, 마운딩 잔디 | ✓ |
| 글자 없음 | ✓ |

비용은 3장 약 $0.12 입니다.

## 프롬프트 — 마지막 회차(3회차, 참고: 기본설계도 + 2회차 그림)

앞 회차 그림을 함께 주고 "그것만 고치고 나머지는 그대로"라고 한 것입니다. 1~2회차 프롬프트는 뺐습니다.

    The FIRST attached image is the site plan of a small ecological park (north is up). The SECOND attached image is a 3D rendering of it that is correct in layout and camera. Reproduce the second image EXACTLY — same camera, pond, wetland, boardwalk loop, forest, pergola plaza, entrance plazas, paths, trees, stream, roads, houses, lighting — and change ONLY this:

    GATHERING PLAZA (the small square paved plaza east of the wetland, with one shade tree in a square tree grate, where the boardwalk meets the entrance path): along its WEST edge place EXACTLY 3 small blank information boards on posts, in a straight north-south row, evenly spaced. Currently there are 2.

    Also make sure the wetland boardwalk loop has EXACTLY 5 outward observation decks (small square timber platforms with rails), each with one small blank board — no more, no fewer.

    Nothing else changes. Photorealistic landscape-architecture visualization. Do NOT write any text, letters, numbers, labels or signs.
