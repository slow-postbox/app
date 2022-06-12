# slow postbox

느린 이메일 프로젝트는 웹 사이트에서 편지를 작성하면 느린 우체통처럼 일정 시간뒤에 도착하는 프로그램입니다.

## 필요한 프로그램

본 프로그램을 실행하려면 다음의 프로그램들이 필요합니다.

1. SMTP
2. MariaDB(MySQL)
3. Redis
4. NGINX
5. [key-store](https://github.com/slow-postbox/key-store)
6. [workbox](https://github.com/slow-postbox/workbox)

## 설치 및 실행

1. 필요한 프로그램 설치
2. 의존성 설치
3. 환경변수 설정
    1. `.env.example` 파일을 복사해 `.env` 파일을 만듭니다.
    2. `.env` 파일을 상황에 맞게 수정합니다.
4. 임시 약관 등록
    * 해당 프로그램은 등록된 약관이 없으면 회원가입을 거부합니다.
    1. `init.py` 스크립트를 실행해 임시 서비스 이용약관과 개인정보 처리방침을 등록합니다.
5. 회원가입후 관리자 등록
    1. `start.py` 스크립트를 이용해 프로그램을 실행 한 다음 사이트에 접속해 회원가입 과정을 진행합니다.
    2. `permission.py` 스크립트를 이용해 유저를 특정하고 해당 유저를 관리자로 권한을 수정합니다.
6. 키 저장소 실행
    1. [key-store](https://github.com/slow-postbox/key-store)를 설정합니다.
    2. 서비스를 실행하거나 `key.py` 스크립트를 실행해 토큰을 생성합니다.
    3. 생성된 토큰을 복사합니다.
7. 서비스 실행
    1. `start.py` 스크립트를 실행해 웹 서비스를 실행합니다.
        * 이때 처음 실행하는 것이라면 `key-store`의 인증 토큰을 입력해야합니다.
        * 만약 토큰이 변경되었다면 `.KEY_STORE` 파일을 삭제후 서비스를 다시 실행하면 됩니다.
8. 백그라운드 작업
   1. [workbox](https://github.com/slow-postbox/workbox)를 설정합니다.
        * 동일한 환경변수 설정이 필요합니다.
        * 해당 서비스가 실행되지 않는다면 메일 전송 작업이 진행되지 않습니다.
   2. 백그라운드 서비스를 실행합니다.

## LICENSE

* This project use [mistune](https://github.com/lepture/mistune) for markdown rendering. [LICENSE](https://github.com/lepture/mistune/blob/master/LICENSE)