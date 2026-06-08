# 오피넷 주변 최저가 주유소 (opinet_nearby)

오피넷 공식 API를 이용해 지정 위치 반경 내 최저가 주유소 2곳을 HA 센서로 제공합니다.

---

## 설치 방법

### 1. 오피넷 API 키 발급
1. [opinet.co.kr](https://www.opinet.co.kr) 접속 → 회원가입
2. 상단 메뉴 **유가정보 API** → **무료 API 신청**
3. 발급된 API 키 복사

### 2. 통합구성요소 설치

#### 방법 A: HACS로 설치 (권장)
1. Home Assistant에서 **HACS**로 이동합니다.
2. 우측 상단 **점 3개 메뉴** ➡️ <strong>Custom repositories (커스텀 저장소)</strong>를 선택합니다.
3. 아래의 리포지토리 정보를 입력하고 <strong>ADD (추가)</strong>를 클릭합니다:
   - **Repository**: `https://github.com/Leek13rl45/ha_opinet`
   - **Category**: `Integration (통합구성요소)`
4. 목록에 추가된 <strong>오피넷 주변 최저가 주유소</strong>를 찾아 다운로드합니다.
5. Home Assistant를 재시작합니다.

#### 방법 B: 수동 설치
1. `custom_components/opinet_nearby/` 폴더 전체를 HA 설정 디렉토리에 복사합니다.
```
<HA config>/
└── custom_components/
    └── opinet_nearby/
        ├── __init__.py
        ├── config_flow.py
        ├── const.py
        ├── manifest.json
        ├── sensor.py
        ├── strings.json
        └── translations/
            └── ko.json
```

### 3. HA에서 통합 추가
1. **설정 → 기기 및 서비스 → 통합 추가** 클릭
2. `오피넷 주변 최저가 주유소` 검색 후 선택
3. 아래 항목 입력:

| 항목 | 설명 |
|---|---|
| **오피넷 API 키** | 발급받은 키 입력 |
| **위도 / 경도** | 기준 위치 (기본값: HA 설정 위치) |
| **검색 반경** | 1 / 3 / 5 / 10 km 선택 |
| **연료 종류** | 휘발유 / 경유 / 고급휘발유 / LPG |
| **갱신 주기** | 기본 60분 (최소 10분) |

4. 저장 후 HA 재시작

---

## 생성되는 센서

| 엔티티 | 설명 |
|---|---|
| `sensor.주유소_최저가_1위` | 반경 내 최저가 1위 주유소 가격 (KRW/L) |
| `sensor.주유소_최저가_2위` | 반경 내 최저가 2위 주유소 가격 (KRW/L) |

### 센서 속성 (attributes)
- `주유소명`, `가격`, `거리`, `주소`, `브랜드`, `셀프여부`, `연료종류`, `검색반경`, `순위`

---

## Lovelace 카드 예시

### 기본 entities 카드
```yaml
type: entities
title: 내 주변 최저가 주유소
entities:
  - entity: sensor.주유소_최저가_1위
    name: 🥇 1위
  - entity: sensor.주유소_최저가_2위
    name: 🥈 2위
```

### 상세 정보 포함 (template 카드, HACS의 button-card 필요 없음)
```yaml
type: markdown
title: ⛽ 주변 최저가 주유소
content: >
  ## 🥇 {{ state_attr('sensor.주유소_최저가_1위', '주유소명') }}
  **가격:** {{ state_attr('sensor.주유소_최저가_1위', '가격') }}
  **거리:** {{ state_attr('sensor.주유소_최저가_1위', '거리') }}
  **브랜드:** {{ state_attr('sensor.주유소_최저가_1위', '브랜드') }}
  ({{ state_attr('sensor.주유소_최저가_1위', '셀프여부') }})

  ---

  ## 🥈 {{ state_attr('sensor.주유소_최저가_2위', '주유소명') }}
  **가격:** {{ state_attr('sensor.주유소_최저가_2위', '가격') }}
  **거리:** {{ state_attr('sensor.주유소_최저가_2위', '거리') }}
  **브랜드:** {{ state_attr('sensor.주유소_최저가_2위', '브랜드') }}
  ({{ state_attr('sensor.주유소_최저가_2위', '셀프여부') }})

  *검색반경: {{ state_attr('sensor.주유소_최저가_1위', '검색반경') }} / {{ state_attr('sensor.주유소_최저가_1위', '연료종류') }}*
```

---

## 설정 변경 (옵션 플로우)
설치 후 **기기 및 서비스** → 해당 통합의 **구성** 버튼으로 반경/연료/갱신주기 언제든 변경 가능합니다.

---

## 주의사항
- 오피넷 API는 **무료** / 하루 요청 횟수 제한 있음 (갱신 주기 60분 권장)
- 가격 정보는 주유소가 자체 신고한 데이터 기준이며 실시간이 아닐 수 있음
- API 키는 절대 공개하지 마세요
