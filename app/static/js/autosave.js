let task_id = undefined;

function get_storage_id(mail_id){
    return `slow_postbox:mail:${mail_id}`;
}

function setup_autosave(mail_id){
    function startTask(){
        task_id = setInterval(() => {
            let markdown = editor.getMarkdown();
    
            if(markdown.length != 0){
                sessionStorage.setItem(STORAGE_KEY, markdown);
            }
        }, 1000);    
    }
    
    const STORAGE_KEY = get_storage_id(mail_id);

    let backupData = sessionStorage.getItem(STORAGE_KEY);

    if(backupData == null){
        // 저장된 편지 없음
        startTask();
    } else {
        if(editor.getMarkdown() != backupData && confirm("* 임시 저장된 편지가 발견되었습니다.\n* 해당 편지를 불러오겠습니까?")){
            editor.setMarkdown(backupData);
        }

        startTask();
    }
}

function clear_autosave(){
    clearInterval(task_id);
}

function remove_autosave(mail_id){
    const STORAGE_KEY = get_storage_id(mail_id);
    sessionStorage.removeItem(STORAGE_KEY);
}
