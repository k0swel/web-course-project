const tag_running_text = document.getElementById('logo-text')

function sleep(ms) {
    return new Promise((resolve) => {setTimeout(resolve, ms)});
}

async function running_text() {
    const speed = 50;
    const original_text = 'Построй надежную облачную инфраструктуру вместе с нами!';
    let text = "";
    
    for (let char of original_text) {  // char = "П", "о", "с"...
        text += char;                   // или text = text.concat(char)
        tag_running_text.textContent = text;
        await sleep(speed);
        console.log(text);
    }

    for (let char of original_text) {
        if (text.length == 1) {
            text=" "
            break;
        }
        text = text.slice(0, -1);
        tag_running_text.textContent = text;
        await sleep(speed);
        console.log(text);
    }
}

async function main() {
while (true) { await running_text(); }
}

main()