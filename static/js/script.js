let fileInfo = {};
let currentSentenceId = null;

/**
 * 在指定的 pre 元素中插入加载圈
 * @param {HTMLElement} preElement - 要添加加载圈的 pre 元素
 */
function addLoadingSpinner(preElement, message) {
    preElement.classList.remove('pre-loading', 'pre-success');
    const spinner = document.createElement('span');
    spinner.classList.add('spinner');
    preElement.classList.add('pre-loading'); // 启动加载效果
    preElement.innerHTML = ''; // 清空原始内容
    preElement.appendChild(spinner);
    preElement.innerHTML += ` ${message}`;
}

/**
 * 在指定的 pre 元素中插入绿色√符号
 * @param {HTMLElement} preElement - 要添加√符号的 pre 元素
 * @param {string} message - 成功消息内容
 */
function addSuccessCheckmark(preElement, message) {
    const checkmark = document.createElement('span');
    checkmark.classList.add('success-icon');
    checkmark.innerText = '✓';  // 添加绿色√符号
    preElement.classList.add('pre-success'); // 启动成功效果
    preElement.innerHTML = ''; // 清空原始内容
    preElement.appendChild(checkmark);
    preElement.innerHTML += ` ${message}`; // 显示成功消息
}


// 上传音频文件
document.getElementById("uploadForm").onsubmit = async function (event) {
    event.preventDefault();

    const formData = new FormData(this);
    // document.getElementById("uploadResultContent").innerText = "Uploading... Please wait.";
    const uploadResultContent = document.getElementById("uploadResultContent");
    addLoadingSpinner(uploadResultContent, "Uploading... Please wait.");

    const response = await fetch("/upload", {
        method: "POST",
        body: formData
    });

    const result = await response.json();
    const message = JSON.stringify(result, null, 2);
    addSuccessCheckmark(uploadResultContent, message);

    if (result.preprocessed_audio) {
        fileInfo = result;
        document.getElementById("recognizeBtn").disabled = false; // 启用识别按钮
        resetSteps("upload");
    }
};

// 监听 Step 1 中文件选择框
document.getElementById("file-input-1").addEventListener("change", function (event) {
    const file = event.target.files[0];
    const audioPreviewContainer = document.getElementById("audioPreviewContainer-1");

    // 如果用户选择了文件，显示音频控件
    if (file) {
        const audioUrl = URL.createObjectURL(file); // 生成文件的临时 URL
        const audioElement = document.createElement("audio"); // 创建音频元素
        audioElement.controls = true; // 显示控件
        const sourceElement = document.createElement("source");
        sourceElement.src = audioUrl;
        sourceElement.type = file.type; // 获取文件的类型
        audioElement.appendChild(sourceElement); // 将 source 元素加入音频元素

        // 清空之前的预览并添加新的音频控件
        audioPreviewContainer.innerHTML = ""; // 清空容器
        audioPreviewContainer.appendChild(audioElement); // 添加新的音频控件
    } else {
        // 如果没有选择文件，清空预览区域
        audioPreviewContainer.innerHTML = "";
    }
});


// 开始语音识别
document.getElementById("recognizeBtn").onclick = async function () {
    const recognizeResultContent = document.getElementById("recognitionResultContent");
    addLoadingSpinner(recognizeResultContent, "Processing... Please wait.");

    const response = await fetch("/recognize", { method: "POST" });

    const result = await response.json();
    const message = JSON.stringify(result, null, 2);
    addSuccessCheckmark(recognizeResultContent, message);

    if (result.transcription) {
        document.getElementById("splitAudioBtn").disabled = false; // 启用切割按钮
        resetSteps("recognize");
    }
};

// 切割音频
document.getElementById("splitAudioBtn").onclick = async function () {
    const sentencePlaceholder = document.getElementById("sentencePlaceholder");
    addLoadingSpinner(sentencePlaceholder, "Splitting audio... Please wait.");

    const response = await fetch("/split_audio", { method: "POST" });
    const result = await response.json();

    if (result.sentence_audio_info) {
        document.getElementById("sentenceList").innerHTML = "<h3>Sentences and Audio:</h3>";
        result.sentence_audio_info.forEach((sentence, index) => {
            const div = document.createElement("div");
            div.setAttribute("data-sentence-id", sentence.sentence_id); // 保存 sentence_id 属性
            div.innerHTML = `
                <p>Sentence ${index + 1}:</p>
                <audio controls>
                    <source src="${sentence.oss_url}" type="audio/wav">
                </audio>
                <textarea>${sentence.text}</textarea>
            `;
            document.getElementById("sentenceList").appendChild(div);
        });

        document.getElementById("submitEditsBtn").disabled = false;
    }
};

// 提交编辑后的句子
document.getElementById("submitEditsBtn").onclick = async function () {
    const updatedSentences = [];
    document.querySelectorAll("#sentenceList div").forEach((div) => {
        const sentenceId = div.getAttribute("data-sentence-id"); // 获取 sentence_id 属性
        const text = div.querySelector("textarea").value;
        const audioUrl = div.querySelector("audio source").src;
        updatedSentences.push({ sentence_id: sentenceId, text: text, audio_url: audioUrl });
    });

    const resultMessage = document.getElementById("resultMessage");
    resultMessage.style.display = "block";
    addLoadingSpinner(resultMessage, "Submitting edits... Please wait.");

    const response = await fetch("/update_transcription", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ updated_sentences: updatedSentences })
    });

    const result = await response.json();
    const message = result.message || `Error: ${result.error}`;
    addSuccessCheckmark(resultMessage, message);
};

// 上传参考音频和文本
document.getElementById("referenceForm").onsubmit = async function (event) {
    event.preventDefault();

    const formData = new FormData(this);
    const referenceResultContent = document.getElementById("referenceResultContent");
    addLoadingSpinner(referenceResultContent, "Uploading reference... Please wait.");

    const response = await fetch("/upload_reference", {
        method: "POST",
        body: formData
    });

    const result = await response.json();
    const message = JSON.stringify(result.reference_audio, null, 2);

    if (result.reference_audio) {
        fileInfo.reference_audio = result.reference_audio; // 存储参考音频信息
        document.getElementById("cloneVoiceBtn").disabled = false;
        addSuccessCheckmark(referenceResultContent, message);
    } else {
        document.getElementById("referenceResultContent").innerText = `Error: ${result.error || "Unknown error"}`;
    }
};

// 监听 Step 5 中文件选择框
document.getElementById("file-input-5").addEventListener("change", function (event) {
    const file = event.target.files[0];
    const audioPreviewContainer = document.getElementById("audioPreviewContainer-5");

    // 如果用户选择了文件，显示音频控件
    if (file) {
        const audioUrl = URL.createObjectURL(file); // 生成文件的临时 URL
        const audioElement = document.createElement("audio"); // 创建音频元素
        audioElement.controls = true; // 显示控件
        const sourceElement = document.createElement("source");
        sourceElement.src = audioUrl;
        sourceElement.type = file.type; // 获取文件的类型
        audioElement.appendChild(sourceElement); // 将 source 元素加入音频元素

        // 清空之前的预览并添加新的音频控件
        audioPreviewContainer.innerHTML = ""; // 清空容器
        audioPreviewContainer.appendChild(audioElement); // 添加新的音频控件
    } else {
        // 如果没有选择文件，清空预览区域
        audioPreviewContainer.innerHTML = "";
    }
});

// 生成变声音频
document.getElementById("cloneVoiceBtn").onclick = async function () {
    const clonedAudioResultContent = document.getElementById("clonedAudioResultContent");
    addLoadingSpinner(clonedAudioResultContent, "Generating cloned audio... Please wait.");

    const response = await fetch("/generate_cloned_audio", { method: "POST" });
    const result = await response.json();

    if (result.cloned_audio_info) {
        renderClonedAudio(result.cloned_audio_info); // 调用渲染方法
        addSuccessCheckmark(clonedAudioResultContent, "Cloned audio generated successfully!");
        document.getElementById("mergeAudioBtn").disabled = false; // 恢复下一步按钮
    } else {
        clonedAudioResultContent.innerText = `Error: ${result.error || "Unknown error"}`;
    }
};

// 渲染生成的音频列表
function renderClonedAudio(clonedAudioInfo) {
    const audioList = document.getElementById("audioList");
    audioList.innerHTML = ""; // 清空之前的内容

    clonedAudioInfo.forEach(audio => {
        const audioDiv = document.createElement("div");
        audioDiv.setAttribute("data-sentence-id", audio.sentence_id); // 添加 sentence_id 标识
        audioDiv.innerHTML = `
            <p id="p-${audio.sentence_id}">Sentence ${audio.sentence_id}: ${audio.text}</p>
            <div id="row-${audio.sentence_id}" class="audio-row">
                <audio controls>
                    <source src="${audio.oss_url}" type="audio/mp3">
                </audio>
                <button onclick="openRegenerateModal(${audio.sentence_id}, '${audio.text}')">Regenerate</button>
            </div>
        `;
        audioList.appendChild(audioDiv);
    });
}

// 打开重新生成的模态框
function openRegenerateModal(sentenceId, currentText) {
    currentSentenceId = sentenceId; // 设置当前句子 ID
    const modal = document.getElementById("regenerateModal");
    document.getElementById("regenerateText").value = currentText; // 设置默认值为当前文本
    modal.style.display = "block";
}

// 关闭模态框
document.getElementById("closeModal").onclick = function () {
    document.getElementById("regenerateModal").style.display = "none";
};

// 确认重新生成
document.getElementById("confirmRegenerate").onclick = async function () {
    const newText = document.getElementById("regenerateText").value;
    if (!newText.trim()) {
        alert("Text cannot be empty!");
        return;
    }

    document.getElementById("mergeAudioBtn").disabled = true; // 禁用下一步按钮
    document.getElementById("regenerateModal").style.display = "none"; // 关闭模态框
    const clonedAudioResultContent = document.getElementById("clonedAudioResultContent");
    addLoadingSpinner(clonedAudioResultContent, `Regenerating sentence ${currentSentenceId}...`);

    const response = await fetch("/regenerate_cloned_audio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sentence_id: currentSentenceId, text: newText })
    });

    const result = await response.json();

    if (result.updated_sentence) {
        alert(`Sentence ${currentSentenceId} regenerated successfully!`);

        // 更新对应的音频信息
        const audioRow = document.getElementById(`row-${currentSentenceId}`);
        audioRow.querySelector("audio source").src = result.updated_sentence.oss_url;
        audioRow.querySelector("audio").load(); // 重新加载音频
        document.getElementById(`p-${currentSentenceId}`).innerText = `Sentence ${currentSentenceId}: ${result.updated_sentence.text}`;
    } else {
        alert(`Error: ${result.error || "Failed to regenerate audio."}`);
    }

    addSuccessCheckmark(clonedAudioResultContent, "Regeneration complete!");
    document.getElementById("mergeAudioBtn").disabled = false; // 恢复下一步按钮
};

// 合并变声音频
document.getElementById("mergeAudioBtn").onclick = async function () {
    const mergedAudioMessage = document.getElementById("mergedAudioMessage");
    addLoadingSpinner(mergedAudioMessage, "Merging cloned audio... Please wait.");

    const response = await fetch("/merge_cloned_audio", { method: "POST" });
    const result = await response.json();

    if (result.merged_audio) {
        const mergedAudio = result.merged_audio;
        addSuccessCheckmark(mergedAudioMessage, "Merged audio available above.");
        const audioPlayer = document.getElementById("mergedAudioPlayer");
        const audioSource = document.getElementById("mergedAudioSource");
        audioSource.src = mergedAudio.oss_url;
        audioPlayer.style.display = "block";
        audioPlayer.load();

        document.getElementById("generateSubtitleBtn").disabled = false;
    }
};


// 生成字幕（SRT）文件
document.getElementById("generateSubtitleBtn").onclick = async function () {
    const subtitleResultContent = document.getElementById("subtitleResultContent")
    addLoadingSpinner(subtitleResultContent, "Generating subtitles... Please wait.")

    const response = await fetch("/generate_srt", { method: "POST" });
    const result = await response.json();

    if (result.generated_srt) {
        addSuccessCheckmark(subtitleResultContent, "SRT Subtitle Generated!")

        // 显示字幕下载链接
        const downloadLink = document.createElement("a");
        downloadLink.href = result.generated_srt.oss_url;  // 使用OSS URL
        downloadLink.download = "generated_subtitles.srt"; // 设置下载文件名
        downloadLink.innerText = `Download SRT file`;

        // 添加下载链接到页面
        document.getElementById("subtitleResult").appendChild(downloadLink);
    } else {
        document.getElementById("subtitleResultContent").innerText = `Error: ${result.error || "Unknown error"}`;
    }
};

// 重置后续步骤
function resetSteps(step) {
    if (step === "upload") {
        document.getElementById("recognitionResultContent").innerText = "Waiting for recognition result...";
        document.getElementById("sentenceList").innerHTML = `
            <h3>Sentences and Audio:</h3>
            <p id="sentencePlaceholder">No sentences available. Please split the audio first.</p>
        `;
        document.getElementById("resultMessage").style.display = "none";

        document.getElementById("recognizeBtn").disabled = false;
        document.getElementById("splitAudioBtn").disabled = true;
        document.getElementById("submitEditsBtn").disabled = true;
        document.getElementById("cloneVoiceBtn").disabled = true;
    } else if (step === "recognize") {
        document.getElementById("sentenceList").innerHTML = `
            <h3>Sentences and Audio:</h3>
            <p id="sentencePlaceholder">No sentences available. Please split the audio first.</p>
        `;
        document.getElementById("resultMessage").style.display = "none";

        document.getElementById("splitAudioBtn").disabled = false;
        document.getElementById("submitEditsBtn").disabled = true;
        document.getElementById("cloneVoiceBtn").disabled = true;
    }
}
