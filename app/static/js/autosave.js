let task_id = undefined;

function setupAutosave(mail_id){
    function startTask(){
        task_id = setInterval(() => {
            let markdown = editor.getMarkdown();
    
            if(markdown.length != 0){
                sessionStorage.setItem(STORAGE_KEY, markdown);
            }
        }, 1000);    
    }
    
    const STORAGE_KEY = `slow_postbox:mail:${mail_id}`;

    let backupData = sessionStorage.getItem(STORAGE_KEY);

    if(backupData == null){
        // 저장된 편지 없음
        startTask();
    } else {
        if(editor.getMarkdown() != backupData && confirm("* 자동 저장된 편지가 발견되었습니다.\n* 해당 편지를 불러오겠습니까?")){
            editor.setMarkdown(backupData);
        }

        startTask();
    }

}

function clearAutosave(mail_id){
    const STORAGE_KEY = `slow_postbox:mail:${mail_id}`;
    clearInterval(task_id);
}
