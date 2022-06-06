# slow postbox

느린 이메일 프로젝트는 웹 사이트에서 편지를 작성하면 느린 우체통처럼 일정 시간뒤에 도착하는 프로그램입니다.

## 필요한 프로그램

본 프로그램을 실행하려면 다음의 프로그램들이 필요합니다.

1. SMTP
2. MariaDB(MySQL)
3. Redis
4. NGINX
5. [key-store](https://github.com/chick0/key-store)

## 설치 및 실행

1. 필요한 프로그램 설치
2. 의존성 설치
3. 환경변수 설정
    1. `.env.example` 파일을 복사해 `.env` 파일을 만든다.
    2. `.env` 파일을 상황에 맞게 수정한다.
4. 임시 약관 등록
    * 해당 프로그램은 등록된 약관이 없으면 회원가입을 거부한다.
    1. `init.py` 스크립트를 실행해 임시 서비스 이용약관과 개인정보 처리방침을 등록한다.
5. 회원가입후 관리자 등록
    1. `start.py` 스크립트를 이용해 프로그램을 실행 한 다음 사이트에 접속해 회원가입 과정을 진행한다.
    2. `permission.py` 스크립트를 이용해 유저를 특정하고 해당 유저를 관리자로 권한을 수정한다.
        * 이때 유저 ID는 가입한 순서대로 부여된다.
6. 서비스 실행
    1. `start.py` 스크립트를 실행해 웹 서비스를 실행한다.
        * 이때 처음 실행하는 것이라면 `key-store`의 인증 토큰을 입력해야한다.
        * 토큰이 변경되었다면 `.KEY_STORE` 파일을 삭제후 서비스를 다시 실행하면 된다.
    3. `worker.py` 스크립트를 실행해 백그라운드 작업을 실행한다.
        * 해당 스크립트가 메일 전송 및 삭제가 필요한 정보를 삭제한다.

## LICENSE

* This project use [mistune](https://github.com/lepture/mistune) for markdown rendering. [LICENSE](https://github.com/lepture/mistune/blob/master/LICENSE)