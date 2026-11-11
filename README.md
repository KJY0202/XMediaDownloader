# X 미디어 다운로더

Windows와 macOS에서 실행할 수 있는 데스크톱 GUI 앱입니다. 계정을 여러 개 등록하고, 기간과 미디어 종류(사진/영상/모두)를 선택해 순차 다운로드합니다.

## 기능

- 여러 계정 ID 또는 프로필 주소 입력 (한 줄에 하나)
- 기간 지정, 전체 기간부터, 오늘까지
- 사진만 / 영상만 / 사진 + 영상
- Chrome, Firefox, Safari, Edge, Brave, Chromium, Opera, Vivaldi 쿠키 사용
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

1. 사용할 브라우저에서 X에 로그인합니다.
2. 앱에서 같은 브라우저를 선택합니다.
3. 계정 ID를 한 줄에 하나씩 입력합니다. 예: `openai` 또는 `https://x.com/openai`
4. 기간, 미디어 종류, 저장 위치를 고른 뒤 다운로드를 시작합니다.

브라우저 쿠키를 읽을 수 있도록 브라우저를 완전히 종료해야 하는 경우가 있습니다. macOS의 키체인 권한, Windows 브라우저 암호화, Linux 키링/프로필 권한에 따라 인증 쿠키를 가져오지 못할 수도 있습니다.

## 작동 범위와 유의사항

- X 검색 결과는 X의 검색 인덱스, 로그인 상태, 계정 공개 범위, 요청 제한 등에 좌우됩니다. 지정 기간의 모든 게시물을 보장하지 않습니다.
- X 검색의 `until:`은 종료일 미포함이므로 앱에서 종료일 다음 날을 지정해 종료일 게시물까지 포함하도록 처리합니다.
- 계정은 순차 처리하고 요청 간 대기를 적용합니다. 요청 제한이 발생하면 무리하게 재시도하지 말고 시간을 두고 다시 시도하세요.
- 중복 방지 기록은 저장 폴더의 `.x-media-download-archive.sqlite3`에 보관됩니다. 기록을 초기화하려면 앱을 종료한 뒤 이 파일을 삭제하세요.
- 다운로드 권한이 있는 콘텐츠에만 사용하고, 저작권·개인정보·X 이용약관을 준수하세요.

## 라이선스 관련

이 앱은 gallery-dl을 외부 프로세스로 실행하며, gallery-dl은 GPL-2.0-only로 배포됩니다. gallery-dl을 포함한 바이너리를 다른 사람에게 재배포할 때는 해당 프로젝트의 라이선스 및 소스 제공 의무를 확인하고 준수해야 합니다. 참고: https://github.com/mikf/gallery-dl
