# X 미디어 다운로더

Windows와 macOS에서 실행할 수 있는 데스크톱 GUI 앱입니다. 계정을 여러 개 등록하고, 기간과 미디어 종류(사진/영상/모두)를 선택해 순차 다운로드합니다.

## 기능

- 여러 계정 ID 또는 프로필 주소 입력 (한 줄에 하나)
- 기간 지정, 전체 기간부터, 오늘까지
- 사진만 / 영상만 / 사진 + 영상
- 로그인 방법 두 가지 지원
  - 브라우저 쿠키 자동 읽기: Chrome, Firefox, Safari, Edge, Brave, Chromium, Opera, Vivaldi
  - `cookies.txt` 파일 직접 지정 (브라우저 쿠키를 읽지 못할 때 사용)
- 저장 폴더 선택, 진행 로그, 중지
- gallery-dl 다운로드 아카이브로 이미 받은 미디어 건너뛰기
- Windows x64, macOS Apple Silicon(arm64), macOS Intel(x64) 자동 빌드 구성

## 소스에서 실행

Python 3.10 이상 권장.

```bash
python -m pip install -r requirements.txt
python twitter_photo_gui.py
```

## 테스트

```bash
python -m unittest discover -s tests -v
```

## GitHub Actions로 앱 빌드하기

1. 이 프로젝트 전체를 새 GitHub 저장소에 업로드합니다.
2. 저장소의 **Actions** 탭에서 **Build Desktop Apps** 워크플로를 선택합니다.
3. **Run workflow**를 누릅니다.
4. 실행이 끝나면 결과 페이지의 Artifacts에서 아래 ZIP 파일을 각각 내려받습니다.
   - `XMediaDownloader-windows-x64`
   - `XMediaDownloader-macos-arm64`
   - `XMediaDownloader-macos-x64`

`v1.0.0` 같은 버전 태그를 push해도 빌드가 실행됩니다. GitHub Actions는 각 운영체제에서 해당 운영체제용 PyInstaller를 실행합니다. PyInstaller 자체는 크로스 컴파일러가 아니므로 Windows/macOS 바이너리를 Linux에서 직접 만들 수 없습니다.

### Windows 설치/실행

ZIP 압축을 풀고 `XMediaDownloader` 폴더 안의 `XMediaDownloader.exe`를 실행합니다. Windows SmartScreen이 표시될 수 있는데, 이는 코드 서명 인증서가 없는 빌드이기 때문입니다.

### macOS 설치/실행

ZIP 압축을 풀고 `XMediaDownloader.app`을 Applications 폴더로 옮겨 실행합니다. Apple Developer ID 서명 및 공증을 하지 않은 빌드이므로 Gatekeeper 경고가 나타날 수 있습니다. 공개 배포 전에는 Developer ID 서명과 notarization을 권장합니다.

## 처음 실행하기

먼저 아래 두 가지 로그인 방법 중 하나를 고릅니다. 어느 쪽이든 X에 로그인된 상태여야 합니다.

### 방법 A. 브라우저 쿠키 사용 (기본)

1. 사용할 브라우저에서 X에 로그인합니다.
2. 앱의 **로그인 브라우저**에서 같은 브라우저를 선택합니다.
3. **cookies.txt** 칸은 비워 둡니다.

Windows의 Chrome, Edge, Brave 같은 Chromium 계열 브라우저는 쿠키 파일 접근이 막혀 실패하는 경우가 많습니다. 이때는 아래 방법 B를 쓰거나 Firefox를 사용하세요.

### 방법 B. cookies.txt 파일 사용

1. 브라우저에서 X에 로그인한 상태로 `x.com`에 접속합니다.
2. "Get cookies.txt LOCALLY" 같은 확장 프로그램을 열고, 현재 사이트(x.com)의 쿠키만 **Export** 합니다. **모든 사이트 쿠키 내보내기(Export All Cookies)는 사용하지 마세요.**
3. 앱의 **cookies.txt** 칸에서 **파일 선택**을 눌러 저장한 파일을 지정합니다.
4. 파일을 지정하면 **로그인 브라우저** 설정은 무시됩니다.

### 다운로드 시작

1. 계정 ID를 한 줄에 하나씩 입력합니다. 예: `openai` 또는 `https://x.com/openai`
2. 기간, 미디어 종류, 저장 위치를 고릅니다.
3. **다운로드 시작**을 누릅니다. 처음에는 기간을 일주일 정도로 짧게 잡고 테스트해 보세요.

## 문제 해결

| 로그 메시지 | 원인과 해결 |
| --- | --- |
| `cookies: [Errno 13] Permission denied ... Cookies` | 브라우저가 쿠키 파일을 잠그고 있거나 암호화되어 읽을 수 없습니다. 브라우저를 작업 관리자에서 완전히 종료한 뒤 다시 시도하거나, Firefox로 바꾸거나, `cookies.txt` 방식(방법 B)을 사용하세요. |
| `AuthRequired: authenticated cookies needed` | 로그인 쿠키를 가져오지 못했습니다. 위 오류와 같은 원인인 경우가 많습니다. X에 로그인되어 있는지 확인하고 방법 B를 사용하세요. |
| `cookies.txt 파일을 찾을 수 없습니다` | 선택한 경로에 파일이 없습니다. 파일 위치를 다시 선택하세요. |
| 요청 제한(429 등) | 시간을 두고 다시 시도하세요. 무리하게 재시도하지 않는 것이 좋습니다. |

`cookies.txt`가 만료되었거나 X에서 로그아웃하면 인증 오류가 다시 발생합니다. 그때는 새로 내보내서 교체하세요.

## 작동 범위와 유의사항

- X 검색 결과는 X의 검색 인덱스, 로그인 상태, 계정 공개 범위, 요청 제한 등에 좌우됩니다. 지정 기간의 모든 게시물을 보장하지 않습니다.
- X 검색의 `until:`은 종료일 미포함이므로 앱에서 종료일 다음 날을 지정해 종료일 게시물까지 포함하도록 처리합니다.
- 계정은 순차 처리하고 요청 간 대기를 적용합니다. 요청 제한이 발생하면 무리하게 재시도하지 말고 시간을 두고 다시 시도하세요.
- 전체 기간(2006-03-21부터)으로 검색하면 오래 걸리고 중간에 끊길 수 있습니다. 필요한 기간만 지정하는 것을 권장합니다.
- 중복 방지 기록은 저장 폴더의 `.x-media-download-archive.sqlite3`에 보관됩니다. 기록을 초기화하려면 앱을 종료한 뒤 이 파일을 삭제하세요.
- 다운로드 권한이 있는 콘텐츠에만 사용하고, 저작권·개인정보·X 이용약관을 준수하세요.

## 보안 주의

- `cookies.txt`에는 **X 로그인 정보가 그대로 들어 있습니다.** 다른 사람에게 보내거나 GitHub 등에 올리지 마세요. 유출되면 계정이 도용될 수 있습니다.
- 저장소 폴더 안에 쿠키 파일을 두었다면 `.gitignore`에 아래 줄을 추가하세요.

  ```
  *cookies*.txt
  ```

- 사용이 끝난 `cookies.txt`는 삭제하세요.
