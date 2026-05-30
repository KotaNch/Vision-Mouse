const fields = [
    "mouse_smooth",
    "deadzone",
    "swipe_threshold",
    "scroll_threshold",
    "scroll_delay"
];

function bindPair(name){
    const range = document.getElementById(name);
    const value = document.getElementById(`${name}_value`);

    range.addEventListener("input", () => value.value = range.value);
    value.addEventListener("input", () => range.value = value.value)
} 
 
fields.forEach(bindPair);

async function loadConfig() {
    const res = await fetch("/api/config");
    const cfg = await res.json();

    for (const key of fields) {
        document.getElementById(key).value = cfg[key];
        document.getElementById(`${key}_value`).value = cfg[key];
    }

    loadCommands(cfg.commands);
}

async function saveConfig() {
    const payload = {};
    for (const key of fields) {
        payload[key] = Number(document.getElementById(key).value);
    }

    const commands = [];
    for (const row of document.querySelectorAll('[data-command-row="1"]')) {
        const fingers = row._fingerInputs.map(inp => Number(inp.value));
        const commandText = row._commandInput.value.trim();
        if (!commandText) continue;

        commands.push({
            fingers,
            command: commandText.split(" ")
        });
    }

    payload.commands = commands;

    const res = await fetch("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    const data = await res.json();
    document.getElementById("statusBox").textContent = JSON.stringify(data, null, 2);
}  
   
async function loadStatus() {
    const res = await fetch("/api/status")
    const data = await res.json();
    document.getElementById("statusBox").textContent = JSON.stringify(data,null,2);
    
}     

document.getElementById("saveButton").addEventListener("click", saveConfig);

loadConfig();
loadStatus();
setInterval(loadStatus, 1000)   

const commandContainer = document.getElementById("commandsList");
const addCommandButton = document.getElementById("addCommandButton");

function createCommandRow(data = {fingers: [1,0,0,1],command: "brave"}){
    const row = document.createElement("div");
    row.style.display = "grid";
    row.style.gridTemplateColumns = "repeat(4, 60px) 1fr 80px"
    row.style.gap = "8px";
    row.style.marginBottom = "10px";

    const fingerInputs = [];
    for (let i = 0; i <4; i++) {
        const input = document.createElement("input");
        input.type = "number";
        input.min = "0";
        input.max = "1";
        input.value = data.fingers[i];
        fingerInputs.push(input);
        row.appendChild(input);
    }           

    const commandInput = document.createElement("input");
    commandInput.type = "text";
    commandInput.placeholder = "brave";
    commandInput.value = Array   .isArray(data.command) ? data.command.join(" ") : data.command;
    row.appendChild(commandInput);
    
    const removeButton = document.createElement("button");
    removeButton.textContent = "X";
    removeButton.onclick = () => row.remove();
    row.appendChild(removeButton);

    row.dataset.commandRow = "1";
    row._fingerInputs = fingerInputs;
    row._commandInput = commandInput;

    commandContainer.appendChild(row);
}    
 
function loadCommands(commands){
    commandContainer.innerHTML = "";
    if (commands && commands.length){
        for (const cmd of commands) createCommandRow(cmd);
    } else{
        createCommandRow();
    }
}

addCommandButton.addEventListener("click", () => createCommandRow());


